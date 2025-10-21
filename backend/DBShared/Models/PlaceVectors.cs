using Npgsql.EntityFrameworkCore.PostgreSQL.Storage.Internal.Json;
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DBShared.Models
{
    public class PlaceVectors
    {
        [Key]
        public int IdVector { get; set; }
        [Column(TypeName = "jsonb")]
        public List<float>? NameEmbedding { get; set; }
        [Column(TypeName = "jsonb")]
        public List<float>? PreferencesEmbedding { get; set; }
        public int IdPlace {  get; set; }       
        public Places? Place { get; set; }

    }
}
