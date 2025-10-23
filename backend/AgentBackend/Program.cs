using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.AspNetCore.Builder;
using DBShared;

namespace AgentBackend
{
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

            // Add services to the container.
            builder.Services.AddDbContext<ApplicationContext>();
            builder.Services.AddEndpointsApiExplorer();
            builder.Services.AddControllers();
         
            builder.Services.AddOpenApi();
            builder.Services.AddSwaggerGen();
            var app = builder.Build();

            // Configure the HTTP request pipeline.
            if (app.Environment.IsDevelopment())
            {
                app.MapOpenApi();
                app.UseSwagger();
                app.UseSwaggerUI();
            }
            
            app.UseHttpsRedirection();

            app.UseAuthorization();


            app.MapControllers();

            app.Run();
        }
    }
}
