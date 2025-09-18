using HtmlAgilityPack;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;

namespace TgParse.Helpers
{
    public class HttpHelper
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
    }
}
