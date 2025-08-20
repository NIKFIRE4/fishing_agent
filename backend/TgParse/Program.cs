using HtmlAgilityPack;
using Microsoft.EntityFrameworkCore;
using Minio;
using Minio.DataModel.Args;
using System.Text.RegularExpressions;
using System.Text.Json;
using System.Net.Http.Headers;
using System.Text;
using Microsoft.Extensions.DependencyInjection;
using Minio.Exceptions;
using WTelegram;
using TL;
using System.Reactive;
using static WTelegram.Client;
using System;
using Microsoft.Extensions.Options;
using System.Net.Mime;
using System.Runtime.CompilerServices;
using static System.Runtime.InteropServices.JavaScript.JSType;
using System.Security.AccessControl;



namespace TgParse
{

    public class MinioUploader
    {
        private readonly IMinioClient _minio;
        private readonly string _bucketName;

        public MinioUploader()
        {
            // Получение параметров из переменных окружения
            var endpoint = Environment.GetEnvironmentVariable("MINIO_ENDPOINT")
                ?? throw new ArgumentNullException("MINIO_ENDPOINT is not set");

            var accessKey = Environment.GetEnvironmentVariable("MINIO_ACCESS_KEY")
                ?? throw new ArgumentNullException("MINIO_ACCESS_KEY is not set");

            var secretKey = Environment.GetEnvironmentVariable("MINIO_SECRET_KEY")
                ?? throw new ArgumentNullException("MINIO_SECRET_KEY is not set");

            _bucketName = Environment.GetEnvironmentVariable("MINIO_BUCKET_NAME")
                ?? "images";

            var useSsl = bool.Parse(
                Environment.GetEnvironmentVariable("MINIO_USE_SSL")
                ?? "false"
            );

            _minio = new MinioClient()
                .WithEndpoint(endpoint)
                .WithCredentials(accessKey, secretKey)
                .WithSSL(useSsl)
                .Build();
        }

        public async Task UploadImage(byte[] imageData, string objectName, string contentType = "image/jpeg")
        {            
            using var stream = new MemoryStream(imageData);
            stream.Position = 0; // КРИТИЧЕСКИ ВАЖНО: сброс позиции потока!

            try
            {
                var bucketExistsArgs = new BucketExistsArgs()
                    .WithBucket(_bucketName);

                bool found = await _minio.BucketExistsAsync(bucketExistsArgs);

                if (!found)
                {
                    var makeBucketArgs = new MakeBucketArgs()
                        .WithBucket(_bucketName);

                    await _minio.MakeBucketAsync(makeBucketArgs);
                }

                var putObjectArgs = new PutObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(objectName)
                    .WithStreamData(stream)
                    .WithObjectSize(stream.Length)
                    .WithContentType(contentType);

                await _minio.PutObjectAsync(putObjectArgs);

                // Проверяем, что файл действительно загружен
                var statArgs = new StatObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(objectName);                
            }
            catch (MinioException e)
            {
                Console.WriteLine($"MinIO Error: {e.Message}");               
            }
        }

        public async Task<byte[]> DownloadImageAsync(string objectName)
        {
            try
            {
                using var memoryStream = new MemoryStream();

                var args = new GetObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(objectName)
                    .WithCallbackStream(stream =>
                    {
                        // Копируем данные из MinIO в MemoryStream 
                        stream.CopyTo(memoryStream);
                    });

                await _minio.GetObjectAsync(args).ConfigureAwait(false);

                // Сбрасываем позицию потока для чтения
                memoryStream.Position = 0;
                return memoryStream.ToArray();
            }
            catch (Exception ex) when (ex is MinioException or IOException)
            {
                // Обрабатываем ошибки MinIO и работы с потоками
                throw new FileNotFoundException(
                    $"Изображение '{objectName}' не найдено в бакете '{_bucketName}'",
                    ex
                );
            }
        }       
    }
    public class TgMessages
    {
        public int Id { get; set; }
        public int MessageId { get; set; }
        public string? MessageText { get; set; }
        public string? СhannelUrl { get; set; }
        public List<TgPhotos>? Photos { get; set; } = new List<TgPhotos>();
    }

    public class TgPhotos
    {
        public int Id { get; set; }
        public string? PhotoUrl { get; set; }
        public int MessageId { get; set; }

        public TgMessages? Message { get; set; }
    }

    public class ApplicationContext : DbContext
    {
        public DbSet<TgMessages> TgMessages { get; set; }
        public DbSet<TgPhotos> TgPhotos { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            var connectionString = Environment.GetEnvironmentVariable("DB_CONNECTION_STRING")
            ?? "${DB_CONNECTION_STRING}"
            ;

            optionsBuilder.UseNpgsql(connectionString);
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<TgMessages>()
                .HasMany(m => m.Photos)
                .WithOne(p => p.Message)
                .HasForeignKey(p => p.MessageId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<TgMessages>()
            .HasIndex(m => m.MessageId)
            .IsUnique();
        }
    }

    class Program
    {
        public static async Task<byte[]> GetRequestAsync(string url)
        {
            using (var client = new HttpClient())
            {
                var response = await client.GetAsync(url);
                return await response.Content.ReadAsByteArrayAsync();
            }
        }

        static public async Task<MultipartFormDataContent> GetResponseAsync(string url)
        {
            byte[] imageBytes;
            using (var client = new HttpClient())
            {
                var response = await client.GetAsync(url);
                imageBytes = await response.Content.ReadAsByteArrayAsync();
            }
            var content = new MultipartFormDataContent();

            // Создаем контент-часть с изображением
            var imageContent = new ByteArrayContent(imageBytes);
            imageContent.Headers.ContentType = MediaTypeHeaderValue.Parse("image/jpeg");

            // Добавляем в multipart контейнер        
            content.Add(imageContent, "image", "image");
            return content;
        }

        public static async Task<bool> DetectPersonAsync(byte[] byteImage)
        {
            string base64Image = Convert.ToBase64String(byteImage);
            var jsonObject = new
            {
                image = base64Image
            };
            // Сериализуем в JSON
            string json = JsonSerializer.Serialize(jsonObject);
            using HttpClient client = new HttpClient();
            client.BaseAddress = new Uri("http://ml_service:8001/");

            // Сериализация данных в JSON

            HttpContent content = new StringContent(json, Encoding.UTF8, "application/json");

            // Отправка POST-запроса
            HttpResponseMessage response = await client.PostAsync("detect-person", content);

            // Чтение ответа
            if (response.IsSuccessStatusCode)
            {
                string responseBody = await response.Content.ReadAsStringAsync();

                JsonDocument doc = JsonDocument.Parse(responseBody);
                return doc.RootElement.GetProperty("person_detected").GetBoolean();

            }
            else
            {
                Console.WriteLine($"Ошибка: {response.StatusCode}");
                return false;
            }
        }

        public static async Task<HtmlDocument?> TakeHtml(string url)
        {
            using var httpClient = new HttpClient();
            httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36");
            try
            {
                // Получаем HTML-код страницы
                string htmlContent = await httpClient.GetStringAsync(url);

                var htmlDoc = new HtmlDocument();
                htmlDoc.LoadHtml(htmlContent);
                return htmlDoc;
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Ошибка при запросе: {ex.Message}");
                return null;
            }
        }                               

        public static HtmlNode? TakeText(HtmlDocument htmlDoc)
        {
            var metaNode = htmlDoc.DocumentNode.SelectSingleNode("//meta[@property='og:description']");
            return metaNode;
        }

        public static HtmlNode? TakeImage(HtmlDocument htmlDoc)
        {
            var metaNode = htmlDoc.DocumentNode.SelectSingleNode("//meta[@property='og:image']");
            return metaNode;
        }

        private static void ConfigureServices(IServiceCollection services)
        {
            services.AddDbContext<ApplicationContext>();
        }

        private static void ApplyMigrations(ApplicationContext context)
        {
            try
            {
                Console.WriteLine("Applying database migrations...");
                context.Database.Migrate();
                Console.WriteLine("Migrations applied successfully!");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying migrations: {ex.Message}");
                Environment.Exit(1);
            }
        }

        static string? Config(string what)
        {
            switch (what)
            {
                case "api_id": return Environment.GetEnvironmentVariable("TELEGRAM_API_ID");
                case "api_hash": return Environment.GetEnvironmentVariable("TELEGRAM_API_HASH");
                case "phone_number": return Environment.GetEnvironmentVariable("TELEGRAM_PHONE_NUMBER");
                case "verification_code": Console.WriteLine("Введите код: ");
                    return Console.ReadLine();
                case "session_pathname": return "/app/wtelegram/wtelegram.session";
                case "server": return "149.154.167.50:443";
                default: return null;
            }
        }

        static async Task<List<(string Type, byte[] Data)>> ProcessMessageMedia(WTelegram.Client client, Message msg)
        {
            var images = new List<(string Type, byte[] Data)>();
            try
            {
                if (msg.media is MessageMediaPhoto { photo: Photo photo })
                {
                    using var stream = new MemoryStream();
                    await client.DownloadFileAsync(photo, stream);
                    images.Add(("Photo", stream.ToArray()));
                }
                else if (msg.media is MessageMediaDocument { document: Document document })
                {
                    if (document.mime_type.StartsWith("image/"))
                    {
                        using var stream = new MemoryStream();
                        await client.DownloadFileAsync(document, stream);
                        images.Add(("Document", stream.ToArray()));
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ERROR] Ошибка при обработке медиа для сообщения ID {msg.id}: {ex.Message}");
            }
            return images;
        }

        private static async Task RunApplication()
        {
            Console.WriteLine("Starting application...");
            using var client = new WTelegram.Client(Config);

            int maxId = 0;
            var offset_id = 100;
            string channelName = "rybalka_spb_lenoblasti";
            string aboutUrl = $"https://t.me/{channelName}";
            try
            {
                // Попытка входа
                await client.LoginUserIfNeeded();
                Console.WriteLine("Авторизация успешна!");
                var resolved = await client.Messages_GetAllChats();
                var channel = resolved.chats.Values.FirstOrDefault(c => c.MainUsername == channelName);
                if (channel == null)
                {
                    Console.WriteLine($"[DEBUG] Канал {channelName} не найден.");
                    return;
                }
                Console.WriteLine($"[DEBUG] Канал {channelName} найден: ID={channel.ID}");

                using var httpClient = new HttpClient();
                httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36");
                var aboutHtml = await TakeHtml(aboutUrl);
                var abouta = TakeText(aboutHtml);

                if (abouta == null || abouta.Attributes["content"] == null)
                {
                    Console.WriteLine("Ошибка: Не удалось получить описание канала.");
                    return;
                }

                try
                {
                    using (var context = new ApplicationContext())
                    {
                        // Получение последнего ID, сортировка по Id
                        var lastMessage = context.TgMessages
                            .OrderByDescending(m => m.MessageId)
                            .FirstOrDefault();

                        if (lastMessage != null)
                        {
                            Console.WriteLine($"Последний ID сообщения в базе: {lastMessage.MessageId}");
                            offset_id = lastMessage.MessageId;
                        }
                        else
                        {
                            Console.WriteLine("Сообщения не найдены.");
                        }
                    }
                }
                catch
                {

                }

                try
                {                                                                       
                    string htmlAll = await httpClient.GetStringAsync($"https://t.me/s/{channelName}");
                    var htmlDocs = new HtmlDocument();
                    htmlDocs.LoadHtml(htmlAll);

                    var allAnchors = htmlDocs.DocumentNode.SelectNodes
                        (
                        "//a[contains(@class, 'tgme_widget_message_date') and contains(@href, 'rybalka_spb_lenoblasti')]"
                        );

                    if (allAnchors != null)
                    {
                        foreach (var anchor in allAnchors)
                        {
                            string href = anchor.GetAttributeValue("href", "");
                            string idPart = href.Split('/').Last();

                            if (int.TryParse(idPart, out int currentId))
                            {
                                if (currentId > maxId)
                                {
                                    maxId = currentId;
                                }
                            }
                        }
                    }

                    Console.WriteLine($"Максимальный ID: {maxId}");                                                               
                }
                catch (HttpRequestException ex)
                {
                    Console.WriteLine($"Ошибка при получении максимального ID: {ex.Message}");
                }
          
                var messageImages = new Dictionary<long, List<(string Type, byte[] Data)>>();                
                var allMessages = new List<Message>();                
                while (offset_id < maxId+100)
                {
                    Console.WriteLine($"ID:::{offset_id}");
                    var messag = await client.Messages_GetHistory(channel, offset_id, limit: 100);

                    if (messag.Messages.Length == 0)
                    {
                        Console.WriteLine("Сообщения закончились.");
                        break;

                    }
                    var messageBatch = messag.Messages.OfType<Message>().ToList();                    
                    allMessages.AddRange(messageBatch);
                    offset_id += 100;

                    foreach (var msg in messageBatch)
                    {
                        var imagu = await ProcessMessageMedia(client, msg);
                        if (imagu.Any())
                        {
                            messageImages[msg.id] = imagu;
                        }
                    }

                    await Task.Delay(500);
                }
                Console.WriteLine($"Загружено {allMessages.Count} сообщений...");

                var imageDbData = new Dictionary<string, byte[]>();
                var messageDbId = 0;
                var messageDbText = "";                
                foreach (var msgBase in allMessages.OrderBy(m => m.id))
                {
                    if (msgBase is Message msg)
                    {
                        string messageText = msgBase.message ?? "<пустое сообщение>";
                        if (messageText != null && !messageText.Contains("#реклама") && messageText != "")
                        {
                            if (messageDbText != "")
                            {
                                Console.WriteLine($"КОЛИЧЕСТОВ ФОТОК ДЛЯ ДБ:: {imageDbData.Count}");
                                
                                using (ApplicationContext db = new())
                                {
                                    var message = new TgMessages
                                    {
                                        MessageText = messageDbText,
                                        MessageId = messageDbId,
                                        СhannelUrl = channelName,
                                    };                                    
                                    bool exists = db.TgMessages.Any(m => m.MessageId == message.MessageId);
                                    if (exists) 
                                    {
                                        Console.WriteLine($"Сообщение {message.MessageId} уже в базе");
                                    }
                                    else
                                    {
                                        foreach (var imageDB in imageDbData)
                                        {
                                            message.Photos?.Add(new TgPhotos { PhotoUrl = imageDB.Key });
                                            var uploader = new MinioUploader();
                                            await uploader.UploadImage(imageDB.Value, imageDB.Key, "image/jpeg");
                                        }
                                        db.TgMessages.AddRange(message);
                                        db.SaveChanges();
                                        Console.WriteLine($"Сообщение {message.MessageId} занесено в базу");
                                    }                                        
                                }

                                imageDbData.Clear();
                                
                            }
                            
                            string mess = messageText.Trim();
                            messageText = Regex.Replace(mess, @"\p{Cs}|\p{So}", "");
                            messageText = Regex.Replace(messageText, @"\n|\r|\&quot;|\&#33;|источник", " ");
                            Console.WriteLine($"Сообщение ID {msgBase.id}: {messageText}");
                            messageDbText = messageText;
                            messageDbId = msgBase.id;
                        }

                        if (messageImages.ContainsKey(msgBase.id))
                        {
                            var imagi = messageImages[msgBase.id];
                            for (int i = 0; i < imagi.Count; i++)
                            {
                                var (type, data) = imagi[i];
                                if (!await DetectPersonAsync(data))
                                {
                                    string uniqueId = Guid.NewGuid().ToString("N");
                                    var contentType = "image/jpeg";
                                    string extension = contentType switch
                                    {
                                        "image/jpeg" => ".jpg",
                                        "image/png" => ".png",
                                        "image/gif" => ".gif",
                                        _ => ".bin"
                                    };

                                    string objectName = $"tg{messageDbId}_{uniqueId}{extension}";
                                    imageDbData[objectName] = data;                                    
                                }
                                    

                            }
                        }                                                                                            
                    }                    
                }

                if (messageDbText != "")
                {
                    Console.WriteLine($"КОЛИЧЕСТОВ ФОТОК ДЛЯ ДБ:: {imageDbData.Count}");

                    using (ApplicationContext db = new())
                    {
                        var message = new TgMessages
                        {
                            MessageText = messageDbText,
                            MessageId = messageDbId,
                            СhannelUrl = channelName,
                        };
                        bool exists = db.TgMessages.Any(m => m.MessageId == message.MessageId);
                        if (exists)
                        {
                            Console.WriteLine($"Сообщение {message.MessageId} уже в базе");
                        }
                        else
                        {
                            foreach (var imageDB in imageDbData)
                            {
                                message.Photos?.Add(new TgPhotos { PhotoUrl = imageDB.Key });
                                var uploader = new MinioUploader();
                                await uploader.UploadImage(imageDB.Value, imageDB.Key, "image/jpeg");
                            }
                            db.TgMessages.AddRange(message);
                            db.SaveChanges();
                            Console.WriteLine($"Сообщение {message.MessageId} занесено в базу");
                        }
                    }

                    imageDbData.Clear();

                }

                //var imageUrls = new List<string>();
                //var imageDbUrls = new List<string>();
                //string? messageTextDb = "";

                //for (int messageId = 16; messageId < maxId; messageId++)
                //{
                //    await Task.Delay(500);
                //    string url = $"https://t.me/{channelName}/{messageId}";                                       
                //    var metaNode = await TakeHtml(url);
                //    if (metaNode == null)
                //    {
                //        Console.WriteLine($"[DEBUG] Сообщение {messageId}: HTML не получен.");
                //        continue;
                //    }
                //    var metaText = TakeText(metaNode);

                //    byte[]? byteImage = null;                    
                //    var metaImage = TakeImage(metaNode)?.Attributes["src"]?.Value.Trim();
                //    byteImage = await GetRequestAsync(metaImage);

                //    //var metaImage = await GetRequestAsync(metaImage);

                //    if (metaText != null && metaText.Attributes["content"] != null)
                //    {
                //        string contentValue = metaText.Attributes["content"].Value;

                //        // Условия для текстовых сообщений
                //        if (contentValue != abouta.Attributes["content"].Value &&
                //            contentValue != "" &&
                //            !contentValue.Contains("#реклама") &&
                //            contentValue.Contains("#"))
                //        {
                //            // Выводим накопленные изображения (если есть)
                //            if (imageUrls.Count > 0)
                //            {
                //                foreach (var imageUrl in imageUrls)
                //                {
                //                    Console.WriteLine(imageUrl);

                //                }
                //                if (messageTextDb != "")
                //                {
                //                    var message = new TgMessages
                //                    {

                //                        MessageText = messageTextDb,
                //                        MessageId = messageId,
                //                        СhannelUrl = channelName,
                //                    };
                //                    foreach (var imageDbUrli in imageDbUrls)
                //                    {
                //                        message.Photos?.Add(new TgPhotos { PhotoUrl = imageDbUrli });
                //                    }
                //                    using (ApplicationContext db = new())
                //                    {
                //                        db.TgMessages.AddRange(message);
                //                        db.SaveChanges();
                //                    }



                //                }

                //                Console.WriteLine();
                //                imageUrls.Clear();
                //                imageDbUrls.Clear();
                //            }
                //            // Обработка и вывод текста
                //            string messageText = contentValue.Trim();
                //            messageText = Regex.Replace(messageText, @"\p{Cs}|\p{So}", "");
                //            messageText = Regex.Replace(messageText, @"\n|\r|\&quot;|\&#33;|источник", " ");
                //            messageTextDb = messageText;

                //            Console.WriteLine($"ID: {messageId}; Текст сообщения:");
                //            Console.WriteLine(messageText);

                //            // Выводим изображение текущего сообщения
                //            if (!string.IsNullOrEmpty(metaImage) && !(await DetectPersonAsync(byteImage)))
                //            {
                //                try
                //                {

                //                    var uploader = new MinioUploader();
                //                    var objectName = await uploader.UploadImage(byteImage, "image/jpeg");
                //                    imageDbUrls.Add(objectName);
                //                    Console.WriteLine($"Image: {objectName}");
                //                }
                //                catch (Exception ex)
                //                {
                //                    Console.WriteLine($"Error: {ex.Message}");
                //                }



                //            }
                //            // Обработка пустых сообщений (только изображения)

                //        }
                //        else if (contentValue == "")
                //        {
                //            if (!string.IsNullOrEmpty(metaImage) && !(await DetectPersonAsync(byteImage)))
                //            {
                //                try
                //                {
                //                    var uploader = new MinioUploader();
                //                    var objectName = await uploader.UploadImage(byteImage, "image/jpeg");
                //                    imageUrls.Add(objectName);
                //                    imageDbUrls.Add(objectName);

                //                }
                //                catch (Exception ex)
                //                {
                //                    Console.WriteLine($"Error: {ex.Message}");
                //                }

                //            }
                //        }
                //    }


                //}

                //// Вывод оставшихся изображений после цикла
                //if (imageUrls.Count > 0)
                //{
                //    foreach (var imageUrl in imageUrls)
                //    {
                //        Console.WriteLine(imageUrl);
                //    }
                //    Console.WriteLine();
                //}

            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] Ошибка при авторизации или работе с клиентом: {ex.Message}");
            }
        }

        static async Task Main(string[] args)
        {
            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            var serviceProvider = serviceCollection.BuildServiceProvider();

            using (var scope = serviceProvider.CreateScope())
            {
                var context = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
                ApplyMigrations(context);
            }

            await RunApplication();
        }
    } 
}