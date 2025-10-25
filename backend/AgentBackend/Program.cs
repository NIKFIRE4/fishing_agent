using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.AspNetCore.Builder;
using DBShared;



using System.Text;
using Microsoft.AspNetCore.Http.Extensions;

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
            // 1. Включаем буферизацию для повторного чтения тела
            context.Request.EnableBuffering();

            // 2. Собираем информацию о запросе
            var request = context.Request;
            var displayUrl = request.GetDisplayUrl();
            var method = request.Method;
            var headers = new StringBuilder();
            var body = string.Empty;

            // 3. Заголовки
            foreach (var header in request.Headers)
            {
                headers.AppendLine($"  -H '{header.Key}: {header.Value}' \\");
            }

            // 4. Тело запроса (только для POST/PUT с JSON)
            if (request.ContentLength > 0 &&
                request.ContentType?.Contains("application/json") == true)
            {
                request.Body.Seek(0, SeekOrigin.Begin);
                using var reader = new StreamReader(
                    request.Body,
                    Encoding.UTF8,
                    detectEncodingFromByteOrderMarks: false,
                    leaveOpen: true);

                body = await reader.ReadToEndAsync();
                request.Body.Seek(0, SeekOrigin.Begin); // Сбрасываем позицию
            }

            // 5. Формируем лог в формате curl
            var logBuilder = new StringBuilder();
            

            

            if (!string.IsNullOrEmpty(body))
            {               
                logBuilder.AppendLine(body);
            }

            _logger.LogInformation("\n{RequestDetails}", logBuilder.ToString());

            // 6. Передаем запрос дальше
            await _next(context);
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
            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            var serviceProvider = serviceCollection.BuildServiceProvider();

            using (var scope = serviceProvider.CreateScope())
            {
                var context = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
                ApplyMigrations(context);
            }
            using ApplicationContext db = new();

            var builder = WebApplication.CreateBuilder(args);

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
            app.UseHttpsRedirection();

            app.UseAuthorization();


            app.MapControllers();
            app.UseMiddleware<RequestLoggingMiddleware>();
            app.Run();
        }
    }
}
