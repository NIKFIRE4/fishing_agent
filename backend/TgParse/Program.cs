using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Hosting;
using TgParse.Data;
using Minio.DataModel.Notification;
using FFMpegCore;


namespace TgParse
{
    class Program
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

        static async Task Main(string[] args)
        {
            //var serviceCollection = new ServiceCollection();
            //ConfigureServices(serviceCollection);
            //var serviceProvider = serviceCollection.BuildServiceProvider();

            //using (var scope = serviceProvider.CreateScope())
            //{
            //    var context = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
            //    ApplyMigrations(context);
            //}
            //using ApplicationContext db = new();



            GlobalFFOptions.Configure(options =>
            {
                options.BinaryFolder = Path.Combine(AppContext.BaseDirectory, "FFmpeg");
                options.TemporaryFilesFolder = Path.GetTempPath();
            });

            //await TelegramParser.RunApplication();
            //


            var builder = WebApplication.CreateBuilder(args);
            builder.Services.AddEndpointsApiExplorer();
            builder.Services.AddSwaggerGen();
            builder.Services.AddDbContext<ApplicationContext>();
            

            builder.Services.AddControllers();
            builder.Services.AddOpenApi();
            //builder.Services.AddHostedService<TgParserService>();
            var app = builder.Build();
            //using (var scope = app.Services.CreateScope())
            //{
            //    var context = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
            //    context.Database.Migrate();
            //}


            app.MapOpenApi();
            app.UseSwagger();
            app.UseSwaggerUI();

            app.UseHttpsRedirection();



            app.MapControllers();


            app.Run();
            
        }

    }
     
}