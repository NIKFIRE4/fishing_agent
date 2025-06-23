using HtmlAgilityPack;
using Microsoft.EntityFrameworkCore;
using System;
using System.Drawing;
using System.IO;
using System.Text.RegularExpressions;
using System.Xml;
using System.Text.Json;
using System.Net.Http;
using System.Net.Http.Headers;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;
using System.Reflection.Metadata;
using System.Diagnostics;
using Microsoft.VisualBasic;
using System.Net.Http.Json;
using System.Text;

namespace TgParse
{
    public class TgMessages
    {
        public int Id { get; set; }
        public int messageId { get; set; }
        public string? message { get; set; }
        public string? channelUrl { get; set; }
        public List<string>?  imageUrls { get; set; }
    }
    public class ApplicationContext: DbContext
    {
        public DbSet<TgMessages> TgMessages { get; set; }
        public ApplicationContext() 
        {
            Database.EnsureCreated();
        }
        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            optionsBuilder.UseNpgsql("Host=localhost; Port=5432; Database=FishingMessages; Username=postgres; Password=567438");
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
            imageContent.Headers.ContentType = MediaTypeHeaderValue.Parse("image/jpeg"); // Укажите правильный MIME-тип

            // Добавляем в multipart контейнер
            // Параметры: данные, имя поля (обычно "file"), имя файла
            content.Add(imageContent, "image", "image");
            return content;
        }

        public static async Task<bool> DetectPersonAsync(string url)
        {
            var base64Image = GetRequestAsync(url);
            string ii = Convert.ToBase64String(await base64Image);
            var jsonObject = new
            {
                image = ii
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

                Console.WriteLine($"Результат: {responseBody}");
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

        static async Task Main(string[] args)
        {
            var urlka = "https://cdn4.cdn-telegram.org/file/sfpK1vrJH2r3lwLTQKNzr4a78fwG8g44Qvlat6Ud9RZwdihs1KnGynRORKPNcJ0MNTrDqelGKlLICWnUNwyE7c_VFI3uM1bD1rIgP3Drr4K9R7q9KISoOOjSTeLh-TDmtUX6uFlBDnyDEngzj-2KpmgVwH81jqx7zx97ZB11sRocdpGAo4eEnHarmXmUM-E0n42mz_dUU8XpSwR8JGnfh_lS9r_Y8nqECoo5zbc9nN9n9GllB2JYEYFN_-Gd0rAUAgTaA-JkNwSLHWAcu15M-UP-RZzXN1azWMzeGCaK-M1a5sFoK4kg8hB2VIkitGa6-9uN4iA7kLQCbiljw0EjWA.jpg";
            var Geting = await GetResponseAsync(urlka);
            var guting = await GetRequestAsync(urlka);
            string base64Image = Convert.ToBase64String(guting);

            //Console.WriteLine(Geting);
            //using (var httpClient = new HttpClient())
            //{
            //    var response = await httpClient.PostAsync("https://postman-echo.com/post", Geting);
            //    response.EnsureSuccessStatusCode();
            //    Console.WriteLine(await response.Content.ReadAsStringAsync());
            //}

            int maxId = 0;
            string channelName = "rybalka_spb_lenoblasti";
            string aboutUrl = $"https://t.me/{channelName}";
            var aboutHtml = await TakeHtml(aboutUrl);
            var abouta = TakeText(aboutHtml);
            using var httpClnt = new HttpClient();
            try
            {
                string htmlAll = await httpClnt.GetStringAsync($"https://t.me/s/{channelName}");
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

            for (int messageId = 1; messageId < maxId; messageId++)
            {

                string url = $"https://t.me/{channelName}/{messageId}";
                var metaNode = await TakeHtml(url);
                if (metaNode == null) continue;
                var metaText = TakeText(metaNode);
                var metaImage = TakeImage(metaNode).Attributes["content"].Value.Trim();
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
                            //if (messageTextDb != "")
                            //{
                            //    using (ApplicationContext db = new())
                            //    {
                            //        TgMessages fishMessage = new() { message = messageTextDb, messageId = messageId, channelUrl = channelName, imageUrls = imageUrls };
                            //        db.TgMessages.AddRange(fishMessage);
                            //        db.SaveChanges();
                            //    }
                            //}
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
                        if (!string.IsNullOrEmpty(metaImage) && !(await DetectPersonAsync(metaImage)))
                        {
                            Console.WriteLine(metaImage);
                            imageDbUrls.Add(metaImage);

                        }
                    }
                    // Обработка пустых сообщений (только изображения)
                    else if (contentValue == "")
                    {
                        if (!string.IsNullOrEmpty(metaImage) && !(await DetectPersonAsync(metaImage)))
                        {
                            
                            imageUrls.Add(metaImage);
                            imageDbUrls.Add(metaImage);
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

    }

        
    
}
