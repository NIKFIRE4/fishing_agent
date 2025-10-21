using TL;
using FFMpegCore;
using WTelegram;
using FFMpegCore.Pipes;
using SkiaSharp;
using System.Drawing;


namespace TgParse.Helpers
{
    public class ProcessMedia
    {
        public static async Task<List<byte[]>> ProcessMessageMedia(Client client, TL.Message msg)
        {
            var images = new List<byte[]>();
            try
            {
                if (msg.media is MessageMediaPhoto { photo: Photo photo })
                {
                    using var stream = new MemoryStream();
                    await client.DownloadFileAsync(photo, stream);
                    images.Add(stream.ToArray());
                }
                else if (msg.media is MessageMediaDocument { document: Document document })
                {
                    if (document.mime_type.StartsWith("image"))
                    {
                        using var stream = new MemoryStream();
                        await client.DownloadFileAsync(document, stream);
                        images.Add(stream.ToArray());
                    }
                    if (document.mime_type.StartsWith("video"))
                    {
                        Console.WriteLine($"Document MIME type: {document.mime_type}");

                        using var videoStream = new MemoryStream();
                        
                        Console.WriteLine("Video saved to /tmp/test_video.mp4");
                        await client.DownloadFileAsync(document, videoStream);
                        using var fileStream = new FileStream("./test_video.mp4", FileMode.Create, FileAccess.Write);
                        videoStream.Position = 0;
                        await videoStream.CopyToAsync(fileStream);
                        Console.WriteLine($"Video stream length: {videoStream.Length} bytes");
                        if (videoStream.Length != 0)
                        {
                            videoStream.Position = 0;
                            //var frameBytes = await ExtractFirstFrameAsync(videoStream, 0); // Передаем поток, а не массив
                            using var photoSteam = new MemoryStream();
                            var frameBytes = await SaveFirstFrameFromStream(videoStream);
                            if (frameBytes != null)
                            {
                                images.Add(frameBytes.ToArray());
                                Console.WriteLine("Добавлено превью (первый кадр видео)");
                            }

                        }
                        
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ERROR] Ошибка при обработке медиа для сообщения ID {msg.id}: {ex.Message}");
            }
            return images;
        }

        async static Task<byte[]> SaveFirstFrameFromStream(Stream videoStream)
        {
            // Сохраняем Stream во временный файл
            var tempVideoPath = Path.GetTempFileName() + ".mp4";
            using (var fileStream = File.Create(tempVideoPath))
            {
                await videoStream.CopyToAsync(fileStream);
            }

            var snap = await SnapshotAsync(input: tempVideoPath, captureTime: new TimeSpan(2));
            File.Delete(tempVideoPath);
            using var image = SKImage.FromBitmap(snap);
            using var data = image.Encode(SKEncodedImageFormat.Jpeg, 90); // 90 — качество JPEG
            return data.ToArray();
            
        }

        public static async Task<SKBitmap> SnapshotAsync(string input, Size? size = null, TimeSpan? captureTime = null, int? streamIndex = null, int inputFileIndex = 0)
        {
            var source = await FFProbe.AnalyseAsync(input).ConfigureAwait(false);
            var (arguments, outputOptions) = SnapshotArgumentBuilder.BuildSnapshotArguments(input, source, size, captureTime, streamIndex, inputFileIndex);
            using var ms = new MemoryStream();

            await arguments
                .OutputToPipe(new StreamPipeSink(ms), options => outputOptions(options
                    .ForceFormat("rawvideo")))
                .ProcessAsynchronously();

            ms.Position = 0;
            return SKBitmap.Decode(ms);
        }
    }
}
