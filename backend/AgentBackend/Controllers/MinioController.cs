using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Minio;
using Minio.DataModel.Args;


namespace AgentBackend.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class MinioController : ControllerBase
    {
        private readonly IMinioClient minioClient;

        public MinioController(IMinioClient minioClient)
        {          
            this.minioClient = minioClient;
        }

        public class PhotoName()
        {
            public string? photoName { get; set; }
        }

        [HttpPost]
        [ProducesResponseType(typeof(string), StatusCodes.Status200OK)]
        public async Task<IActionResult> GetUrl(PhotoName photo)
        {


            //await minioClient.StatObjectAsync(
            //        new StatObjectArgs()
            //            .WithBucket("images")
            //            .WithObject("tg103_189a1bc1d9de48d1964095791b2da2ed.jpg")
            //    );
            //var url = await minioClient.PresignedGetObjectAsync(new PresignedGetObjectArgs()
            //        .WithBucket("images")
            //        .WithObject("tg107_155c3327c1bf4d85ae9051bf11fb1efc.jpg")
            //          .WithExpiry(60 * 60))                  
            //    .ConfigureAwait(false);

            var uploader = new MinioUploader();
            var result = await uploader.GetUrl(photo.photoName);
            return Ok(result);
        }

        
    }

    
}
