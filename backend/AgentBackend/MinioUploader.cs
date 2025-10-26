using Minio.DataModel.Args;
using Minio;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace AgentBackend
{
    public class MinioUploader
    {
        private readonly IMinioClient _minio;
        private readonly string _bucketName;

        public MinioUploader()
        {
            // Получение параметров из переменных окружения
            var endpoint = "minio:9000";

            var accessKey = "admin";

            var secretKey = "1lomalsteklo";

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

        public async Task<string> GetUrl(string photo)
        {
            var url = await _minio.PresignedGetObjectAsync(new PresignedGetObjectArgs()
                    .WithBucket("images")
                    .WithObject(photo)
                      .WithExpiry(60 * 60))
                .ConfigureAwait(false);
            return url;
        }
    }
}
