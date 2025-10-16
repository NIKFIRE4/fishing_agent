using HtmlAgilityPack;
using System.Text.RegularExpressions;
using TgParse.Data;
using TgParse.Helpers;
using TgParse.Models;
using TL;
using static System.Net.Mime.MediaTypeNames;

namespace TgParse.Services
{
    public class TelegramParser
    {
        
        static string? Config(string what)
        {
            switch (what)
            {
                case "api_id": return Environment.GetEnvironmentVariable("TELEGRAM_API_ID") ?? "${TELEGRAM_API_ID}";
                case "api_hash": return Environment.GetEnvironmentVariable("TELEGRAM_API_HASH") ?? "${TELEGRAM_API_HASH}";
                case "phone_number": return Environment.GetEnvironmentVariable("TELEGRAM_PHONE_NUMBER") ?? "${TELEGRAM_PHONE_NUMBER}";
                case "verification_code":
                    Console.WriteLine("Введите код: ");
                    return Console.ReadLine();
                case "session_pathname":
                    string basePath = Directory.GetCurrentDirectory(); // Получаем текущую директорию
                    string sessionFolder = Path.Combine(basePath, "wtelegram"); // Папка wtelegram в текущей директории
                    Directory.CreateDirectory(sessionFolder); // Создаем папку, если она не существует
                    return Path.Combine(sessionFolder, "wtelegram.session"); ;
                case "server": return "149.154.167.50:443";
                default: return null;
            }
        }

        public static async Task RunApplication()
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

                //var messagesRespons = await client.Messages_GetHistory(channel, 18438, limit: 100);
                //var messageBatc = messagesRespons.Messages.OfType<Message>().OrderBy(m => m.id).ToList();
                //foreach (var msgBas in messageBatc)
                //{
                //    if (msgBas is Message msga)
                //    {
                //        var imageBytesList = await ProcessMedia.ProcessMessageMedia(client, msga);                       
                //        Console.WriteLine($"{msga.id} {imageBytesList.Count}");
                //        var uploader = new MinioUploader();
                //        foreach (var image in imageBytesList) 
                //        {
                //            string uniqueId = Guid.NewGuid().ToString("N");
                //            await uploader.UploadImage(image, $"{msga.id}_test_{uniqueId}", "image/jpeg");
                //        }
                          
                        
                //    }
                //}
                using var httpClient = new HttpClient();
                httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36");
                var aboutHtml = await HttpHelper.TakeHtml(aboutUrl);
                var abouta = HttpHelper.TakeText(aboutHtml);

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
                            offset_id = lastMessage.MessageId + 101;
                        }
                        else
                        {
                            Console.WriteLine("Сообщения не найдены.");
                        }
                    }
                }
                catch (HttpRequestException ex)
                {
                    Console.WriteLine($"Ошибка: {ex.Message}");
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

                var imageDbData = new Dictionary<string, byte[]>();
                var messageDbId = 0;
                var messageDbText = "";
                var messageImages = new Dictionary<long, List<byte[]>>();
                var allMessages = new List<Message>();
                while (offset_id < maxId + 100)
                {                  
                    Console.WriteLine($"ID:::{offset_id}");
                    var messagesResponse = await client.Messages_GetHistory(channel, offset_id, limit: 100);

                    if (messagesResponse.Messages.Length == 0)
                    {
                        Console.WriteLine("Сообщения закончились.");
                        break;

                    }
                    var messageBatch = messagesResponse.Messages.OfType<Message>().OrderBy(m => m.id).ToList();

                    offset_id += 100;

                    foreach (var msgBase in messageBatch)
                    {
                        if (msgBase is Message msg)
                        {
                            string messageText = msgBase.message ?? "<пустое сообщение>";
                            if (messageText != null && !messageText.Contains("#реклама") && messageText != "" && messageText.Contains("#"))
                            {
                                if (messageDbText != "")
                                {
                                    await TgMessageSaver.SaveMessageToDb(messageDbId, messageDbText, imageDbData, channelName);
                                    imageDbData.Clear();

                                }

                                string mess = messageText.Trim();
                                messageText = Regex.Replace(mess, @"\p{Cs}|\p{So}", "");
                                messageText = Regex.Replace(messageText, @"\n|\r|\&quot;|\&#33;|источник", " ");
                                Console.WriteLine($"Сообщение ID {msgBase.id}: {messageText}");
                                messageDbText = messageText;
                                messageDbId = msgBase.id;
                            }
                            var imageBytesList = await ProcessMedia.ProcessMessageMedia(client, msg);

                            foreach (var imageBytes in imageBytesList)
                            {
                                if (!await PersonDetector.DetectPersonAsync(imageBytes))
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
                                    imageDbData[objectName] = imageBytes;
                                }


                            }

                        }
                    }
                    await Task.Delay(500);
                }

                if (messageDbText != "")
                {
                    await TgMessageSaver.SaveMessageToDb(messageDbId, messageDbText, imageDbData, channelName);
                    imageDbData.Clear();

                }
                
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] Ошибка при авторизации или работе с клиентом: {ex.Message}");
            }
        }
    }
}
