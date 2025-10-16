using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TgParse.Models
{
        public class PlaceResponse
        {
            public bool new_place { get; set; }
            public string? name_place { get; set; }
            public List<decimal>? coordinates { get; set; }
            public ShortDescription? short_description { get; set; }
            public string? description { get; set; }
        }

        public class ShortDescription
        {
            public List<string>? name_place { get; set; }
            public List<decimal>? coordinates { get; set; }
            public List<string>? caught_fishes { get; set; }
            public List<string>? water_space { get; set; }
        }
}
