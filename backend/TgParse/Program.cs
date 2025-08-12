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

            public async Task<string> UploadImage(byte[] imageData, string contentType = "image/jpeg")
            {
                string uniqueId = Guid.NewGuid().ToString();
                string extension = contentType switch
                {
                    "image/jpeg" => ".jpg",
                    "image/png" => ".png",
                    "image/gif" => ".gif",
                    _ => ".bin"
                };

                string objectName = $"{uniqueId}{extension}";

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

                    return objectName;
                }
                catch (MinioException e)
                {
                    Console.WriteLine($"MinIO Error: {e.Message}");
                    return null;
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

                private static async Task RunApplication()
                {
                    Console.WriteLine("Starting application...");
                    var urli = "https://cdn4.telesco.pe/file/rXclwr5XfPRG0No039KyAjcmkL1GTvrsWFjB_HQf_VSQovOjtIM6b2soiN89PoOIDS9VIgBvcU5w4Nnnp4cPOmhufwWy9K7zAJFhGFe02RINyjcZ4YvN08HFw0wRF5T-HKLR-PLVYFW6o5qoAb51A9AFqqBmUf1cL2dcEdp7Tg5szHARKjs-VFW4ArykcBz5xKX2aLyYyqDVoiYEl5vgb14UXThHJ2wLXfwSbFb1lIlZ84XXIvb80f5gODmzCiLCv3NZo4Ta0Os8WEMQxaEmGRNUtLXqrY2hyT0ODcD85c-BuNAIYqTlAXurk_6E0oRHSc2TDUQkhEdMYIECUGQACQ.jpg";
                   
                    int maxId = 0;
                    string channelName = "rybalka_spb_lenoblasti";
                    string aboutUrl = $"https://t.me/{channelName}";                

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
                        Console.WriteLine($"Ошибка при запросе: {ex.Message}");
                    }

                    var imageUrls = new List<string>();
                    var imageDbUrls = new List<string>();
                    string? messageTextDb = "";

                    for (int messageId = 16; messageId < maxId; messageId++)
                    {
                        await Task.Delay(500);
                        string url = $"https://t.me/{channelName}/{messageId}";
                        var metaNode = await TakeHtml(url);
                        if (metaNode == null)
                            {
                                Console.WriteLine($"[DEBUG] Сообщение {messageId}: HTML не получен.");
                                continue;
                            }
                    var metaText = TakeText(metaNode);

                        byte[]? byteImage = null;
                        if (messageId <= 30)
                            {
                                Console.WriteLine($"[DEBUG] Сообщение {messageId}: HTML = {metaNode.DocumentNode.OuterHtml.Substring(0, Math.Min(500, metaNode.DocumentNode.OuterHtml.Length))}...");
                            }
                    var metaImage = TakeImage(metaNode)?.Attributes["src"]?.Value.Trim();
                        if (string.IsNullOrEmpty(metaImage))
                        {
                            Console.WriteLine($"[DEBUG] Сообщение {messageId}: Пустой или отсутствующий src у изображения.");
                            continue;
                        }
                        Console.WriteLine($"[DEBUG] Сообщение {messageId}: Извлечён URL изображения: {metaImage}");
                        byteImage = await GetRequestAsync(metaImage);

                        //var metaImage = await GetRequestAsync(metaImage);

                        if (metaText != null && metaText.Attributes["content"] != null)
                        {
                            string contentValue = metaText.Attributes["content"].Value;

                            // Условия для текстовых сообщений
                            if (contentValue != abouta.Attributes["content"].Value &&
                                contentValue != "" &&
                                !contentValue.Contains("#реклама") &&
                                contentValue.Contains("#"))
                            {
                                // Выводим накопленные изображения (если есть)
                                if (imageUrls.Count > 0)
                                {
                                    foreach (var imageUrl in imageUrls)
                                    {
                                        Console.WriteLine(imageUrl);

                                    }
                                    if (messageTextDb != "")
                                    {



                                        var message = new TgMessages
                                        {

                                            MessageText = messageTextDb,
                                            MessageId = messageId,
                                            СhannelUrl = channelName,
                                        };
                                        foreach (var imageDbUrl in imageDbUrls)
                                        {
                                            message.Photos.Add(new TgPhotos { PhotoUrl = imageDbUrl });
                                        }
                                        using (ApplicationContext db = new())
                                        {
                                            db.TgMessages.AddRange(message);
                                            db.SaveChanges();
                                        }



                                    }

                                    Console.WriteLine();
                                    imageUrls.Clear();
                                    imageDbUrls.Clear();
                                }
                                // Обработка и вывод текста
                                string messageText = contentValue.Trim();
                                messageText = Regex.Replace(messageText, @"\p{Cs}|\p{So}", "");
                                messageText = Regex.Replace(messageText, @"\n|\r|\&quot;|\&#33;|источник", " ");
                                messageTextDb = messageText;

                                Console.WriteLine($"ID: {messageId}; Текст сообщения:");
                                Console.WriteLine(messageText);

                                // Выводим изображение текущего сообщения
                                if (!string.IsNullOrEmpty(metaImage) && !(await DetectPersonAsync(byteImage)))
                                {
                                    try
                                    {

                                        var uploader = new MinioUploader();
                                        var objectName = await uploader.UploadImage(byteImage, "image/jpeg");
                                        imageDbUrls.Add(objectName);
                                        Console.WriteLine($"Image: {objectName}");
                                    }
                                    catch (Exception ex)
                                    {
                                        Console.WriteLine($"Error: {ex.Message}");
                                    }



                                }
                                // Обработка пустых сообщений (только изображения)

                            }
                            else if (contentValue == "")
                            {
                                if (!string.IsNullOrEmpty(metaImage) && !(await DetectPersonAsync(byteImage)))
                                {
                                    try
                                    {
                                        var uploader = new MinioUploader();
                                        var objectName = await uploader.UploadImage(byteImage, "image/jpeg");
                                        imageUrls.Add(objectName);
                                        imageDbUrls.Add(objectName);

                                    }
                                    catch (Exception ex)
                                    {
                                        Console.WriteLine($"Error: {ex.Message}");
                                    }

                                }
                            }
                        }


                    }

                    // Вывод оставшихся изображений после цикла
                    if (imageUrls.Count > 0)
                    {
                        foreach (var imageUrl in imageUrls)
                        {
                            Console.WriteLine(imageUrl);
                        }
                        Console.WriteLine();
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
    }