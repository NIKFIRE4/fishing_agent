using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TgParse.Services;
using TgParse.Helpers;
using TgParse.Data;
using TgParse.Models;
using System.Text.RegularExpressions;

namespace TgParse
{
    public class TgParseHtml
    {
        static async Task Parse()
        {
            int maxId = 1000;            
            string channelName = "rybalka_spb_lenoblasti";
            string aboutUrl = $"https://t.me/{channelName}";
            var imageUrls = new List<string>();
            var imageDbUrls = new List<string>();
            string? messageTextDb = "";

            using var httpClient = new HttpClient();
            httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36");
            var aboutHtml = await HttpHelper.TakeHtml(aboutUrl) ?? new HtmlAgilityPack.HtmlDocument();          
            var abouta = HttpHelper.TakeText(aboutHtml);

            for (int messageId = 16; messageId < maxId; messageId++)
            {
                await Task.Delay(500);
                string url = $"https://t.me/{channelName}/{messageId}";
                var metaNode = await HttpHelper.TakeHtml(url);
                if (metaNode == null)
                {
                    Console.WriteLine($"[DEBUG] Сообщение {messageId}: HTML не получен.");
                    continue;
                }
                var metaText = HttpHelper.TakeText(metaNode);

                byte[]? byteImage = null;
                var metaImage = HttpHelper.TakeImage(metaNode)?.Attributes["src"]?.Value.Trim() ?? "неизвестно";
                byteImage = await HttpHelper.GetRequestAsync(metaImage);

                //var metaImage = await GetRequestAsync(metaImage);

                if (metaText != null && metaText.Attributes["content"] != null)
                {
                    string contentValue = metaText.Attributes["content"].Value;

                    // Условия для текстовых сообщений
                    if (contentValue != abouta?.Attributes["content"].Value &&
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
                                    SourceUrl = channelName,
                                };
                                foreach (var imageDbUrli in imageDbUrls)
                                {
                                    message.Photos?.Add(new TgPhotos { PhotoUrl = imageDbUrli });
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
                        if (!string.IsNullOrEmpty(metaImage) && !(await PersonDetector.DetectPersonAsync(byteImage)))
                        {
                            try
                            {

                                var uploader = new MinioUploader();
                                await uploader.UploadImage(byteImage, "image/jpeg");
                                
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
                        if (!string.IsNullOrEmpty(metaImage) && !(await PersonDetector.DetectPersonAsync(byteImage)))
                        {
                            try
                            {
                                var uploader = new MinioUploader();
                                await uploader.UploadImage(byteImage, "image/jpeg");
                               

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
    }
}
