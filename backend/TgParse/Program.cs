using HtmlAgilityPack;
using System;
using System.Xml;

namespace FishingAgent
{
    class Program
    {
        public static async Task<HtmlNode?> TakeText(string url)
        {
            using var httpClient = new HttpClient();
            try
            {
                // Получаем HTML-код страницы
                string htmlContent = await httpClient.GetStringAsync(url);

                var htmlDoc = new HtmlDocument();
                htmlDoc.LoadHtml(htmlContent);


                var metaNode = htmlDoc.DocumentNode.SelectSingleNode("//meta[@property='og:description']");
                return metaNode;
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Ошибка при запросе: {ex.Message}");
                return null;
            }
        }

        static async Task Main(string[] args)
        {
            int maxId = 0;
            string channelName = "rybalka_spb_lenoblasti";
            string aboutUrl = $"https://t.me/{channelName}";
            var abouta = await TakeText(aboutUrl);
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


            for (int messageId = maxId; messageId > 1; messageId--)
            {

                string url = $"https://t.me/{channelName}/{messageId}";
                var metaNode = await TakeText(url);

                if (metaNode != null && metaNode.Attributes["content"] != null && metaNode.Attributes["content"].Value != abouta.Attributes["content"].Value
                    && metaNode.Attributes["content"].Value != "" && !(metaNode.Attributes["content"].Value.Contains("#реклама")))
                {
                    string messageText = metaNode.Attributes["content"].Value.Trim();
                    Console.WriteLine($"ID: {messageId};  Текст сообщения:");
                    Console.WriteLine(messageText);
                }
            }

        }
    }
}
