using Minio.DataModel.Args;
using Minio.Exceptions;
using Minio;

namespace TgParse.Services
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
}
