using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TgParse.Data;

namespace TgParse.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class FishingPlaceController: ControllerBase
    {
        private readonly ApplicationContext _context;

        public FishingPlaceController(ApplicationContext context)
        {
            _context = context;
        }


    }
}
