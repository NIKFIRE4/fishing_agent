using DBShared;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http.Extensions;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Minio;
using System.Diagnostics;
using System.Text;

namespace AgentBackend
{
    

    public class RequestLoggingMiddleware
    {
        private readonly RequestDelegate _next;
        private readonly ILogger<RequestLoggingMiddleware> _logger;

        public RequestLoggingMiddleware(
            RequestDelegate next,
            ILogger<RequestLoggingMiddleware> logger)
        {
            _next = next;
            _logger = logger;
        }

        public async Task InvokeAsync(HttpContext context)
        {
            var stopwatch = Stopwatch.StartNew();

            string requestBody = string.Empty;

            // 2. Проверяем наличие JSON-тела (для любых методов)
            if (context.Request.ContentLength > 0 &&
                context.Request.ContentType?.Contains("application/json") == true)
            {
                context.Request.EnableBuffering();

                using var reader = new StreamReader(
                    context.Request.Body,
                    Encoding.UTF8,
                    leaveOpen: true
                );

                requestBody = await reader.ReadToEndAsync();
                context.Request.Body.Seek(0, SeekOrigin.Begin); // Для последующих обработчиков
            }

            // 3. Передаем запрос дальше
            await _next(context);

            // 4. Останавливаем таймер
            stopwatch.Stop();


            _logger.LogInformation(
                "{Method} {Url} | Status: {StatusCode} | Time: {Elapsed}ms | Body: {RequestBody}",
                context.Request.Method,
                context.Request.GetDisplayUrl(),
                context.Response.StatusCode,
                stopwatch.ElapsedMilliseconds,
                requestBody.Replace("\n", " ").Replace("\r", " ").Trim()
            );

        }
    }
    public class Program
    {
        
        private static void ConfigureServices(IServiceCollection services)
        {
            services.AddDbContext<ApplicationContext>();
        }
        private static void ApplyMigrations(ApplicationContext context)
        {
            try
            {
                Console.WriteLine("Applying database migrations...");
                context.Database.Migrate();
                Console.WriteLine("Migrations applied successfully!");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying migrations: {ex.Message}");
                Environment.Exit(1);
            }
        }

        public static void Main(string[] args)
        {
            DotNetEnv.Env.Load();
            var endpoint = "localhost:9000";

            var accessKey = "admin";

            var secretKey = "1lomalsteklo";

            var _bucketName = "images";
            //var serviceCollection = new ServiceCollection();
            //ConfigureServices(serviceCollection);
            //var serviceProvider = serviceCollection.BuildServiceProvider();

            //using (var scope = serviceProvider.CreateScope())
            //{
            //    var context = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
            //    ApplyMigrations(context);
            //}
            //using ApplicationContext db = new();

            var builder = WebApplication.CreateBuilder(args);
            

            // Add Minio using the custom endpoint and configure additional settings for default MinioClient initialization
            builder.Services.AddMinio(configureClient =>
            {
                configureClient
                    .WithEndpoint(endpoint)
                    .WithCredentials(accessKey, secretKey)
                    .WithRegion("us-east-1")
                    .WithSSL(false);
               
            });
           
            // Add services to the container.
            builder.Services.AddDbContext<ApplicationContext>();
            builder.Services.AddEndpointsApiExplorer();
            builder.Services.AddControllers();
         
            builder.Services.AddOpenApi();
            builder.Services.AddSwaggerGen();
            builder.Logging.AddFilter("YourNamespace.RequestLoggingMiddleware", LogLevel.Information);

            //builder.Services.AddHttpLogging(logging =>
            //{
            //    logging.LoggingFields = Microsoft.AspNetCore.HttpLogging.HttpLoggingFields.All;
            //});
            var app = builder.Build();

            // Configure the HTTP request pipeline.
            if (app.Environment.IsDevelopment())
            {
                app.MapOpenApi();
                app.UseSwagger();
                app.UseSwaggerUI();
            }
            //app.UseHttpLogging();
            app.UseMiddleware<RequestLoggingMiddleware>();
            app.UseHttpsRedirection();

            app.UseAuthorization();


            app.MapControllers();
            
            app.Run();
        }
    }
}
