using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TgParse.Models
{
    public class PlaceDto
    {
        [Key]
        public int id { get; set; }
        public List<string>? name_place { get; set; }
        public List<double>? coordinates { get; set; }
        public ShortDescriptionDto? short_description { get; set; }
        public string? description { get; set; }
    }

    public class ShortDescriptionDto
    {
        public List<string>? name_place { get; set; }
        public List<double>? coordinates { get; set; }
        public List<string>? caught_fishes { get; set; }
        public List<string>? water_space { get; set; }
    }
}
