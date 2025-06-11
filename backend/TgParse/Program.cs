using HtmlAgilityPack;
using Microsoft.EntityFrameworkCore;
using System;
using System.Runtime.Intrinsics.X86;
using System.Text.RegularExpressions;
using System.Xml;

namespace TgParse
{

    public class TgMessages
    {
        public int Id { get; set; }
        public int messageId { get; set; }
        public string? message { get; set; }
        public string? channelUrl { get; set; }
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

            bool flag = false;
            var imageUrls = new List<string>();

            for (int messageId = 17400; messageId < maxId; messageId++)
            {

                string url = $"https://t.me/{channelName}/{messageId}";
                var metaNode = await TakeHtml(url);
                if (metaNode == null) continue;
                var metaText = TakeText(metaNode);
                var metaImage = TakeImage(metaNode).Attributes["content"].Value.Trim();


                //if (metaText != null && metaText.Attributes["content"] != null && metaText.Attributes["content"].Value != abouta.Attributes["content"].Value
                //    && metaText.Attributes["content"].Value != "" && !metaText.Attributes["content"].Value.Contains("#реклама") && metaText.Attributes["content"].Value.Contains("#"))
                //{
                //    imageUrls.Clear();
                //    flag = false;
                //    imageUrls.Add(metaImage);
                //    Console.WriteLine(metaImage);

                //    string messageText = metaText.Attributes["content"].Value.Trim();
                //    //string imageText = metaImage.Attributes["content"].Value.Trim();

                //    messageText = Regex.Replace(messageText, @"\p{Cs}|\p{So}", "");
                //    messageText = Regex.Replace(messageText, @"\n|\r|\&quot;|\&#33;|источник", " ");

                //    //using (ApplicationContext db = new())
                //    //{
                //    //    LenOblast fishMessage = new() { message = messageText, messageId = messageId, channelUrl = channelName, imageUrl = imageText };
                //    //    db.LenOblasts.AddRange(fishMessage);
                //    //    db.SaveChanges();
                //    //}

                //    Console.WriteLine($"ID: {messageId};  Текст сообщения:");
                //    Console.WriteLine(messageText);
                //}
                //else if (metaText.Attributes["content"].Value == "")
                //{
                //    flag = true;
                //    Console.WriteLine(metaImage);
                //    imageUrls.Add(metaImage);
                //}

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
                            Console.WriteLine();
                            imageUrls.Clear();
                        }

                        // Обработка и вывод текста
                        string messageText = contentValue.Trim();
                        messageText = Regex.Replace(messageText, @"\p{Cs}|\p{So}", "");
                        messageText = Regex.Replace(messageText, @"\n|\r|\&quot;|\&#33;|источник", " ");

                        Console.WriteLine($"ID: {messageId}; Текст сообщения:");
                        Console.WriteLine(messageText);

                        // Выводим изображение текущего сообщения
                        if (!string.IsNullOrEmpty(metaImage))
                        {
                            Console.WriteLine(metaImage);

                        }
                    }
                    // Обработка пустых сообщений (только изображения)
                    else if (contentValue == "")
                    {
                        if (!string.IsNullOrEmpty(metaImage))
                        {
                            imageUrls.Add(metaImage);
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
