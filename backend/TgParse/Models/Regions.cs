
using System.ComponentModel.DataAnnotations;

namespace TgParse.Models
{
    public class Regions
    {
        [Key]
        public int IdRegions { get; set; }
        public string? RegionName { get; set; }
        public List<TgMessages>? Messages { get; set; } = new List<TgMessages>();
    }
}
