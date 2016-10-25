<!DOCTYPE html>
<html>
<head>
  <title>EDTS Web</title>
  <link rel="stylesheet" type="text/css" href="/static/style.css" />
  <style type="text/css">
    /* Main page stuff */
    body { text-align: center; }
    .wrap { min-width: 600px; max-width: 800px; width: 800px; text-align: left; margin: 0 auto; }
    .widget { font-size: 1.5em; color: #eef; width: 100%; }
    .wname { width: 1%; white-space: nowrap; padding-right: 20px; }
    .winput { padding-left: 20px; padding-right: 20px; white-space: nowrap; }
    .woutput, .werror { font-size: 0.8em; padding-top: 20px; }
    .woutput-table { width: 90%; margin-top: 50px; margin: 0 auto; }
    .woutput-table td { width: 100%; white-space: nowrap; }
    .werror { text-align: center; }
  </style>
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/json2/20150503/json2.min.js"></script>
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/sprintf/1.0.3/sprintf.min.js"></script>
  <script>
    function doXHR(endpoint, query, resultFunc, errorFunc)
    {
      var xhr = new XMLHttpRequest();
      xhr.onreadystatechange = function()
      {
        if (xhr.readyState === XMLHttpRequest.DONE)
        {
          if (xhr.status === 200)
            resultFunc(JSON.parse(xhr.responseText).result);
          else
            errorFunc(query, xhr.status);
        } 
      }
      xhr.open('GET', '/api/v1/' + endpoint + '/' + query, true);
      xhr.send(null);
    }

    function doJumpRange()
    {
      var fsd = document.getElementById('input-fsdclass').value;
      var mass = parseFloat(document.getElementById('input-shipmass').value);
      var fuel = parseFloat(document.getElementById('input-fueltank').value);
      var cargo = parseInt(document.getElementById('input-cargo').value);
      var optmod = document.getElementById('input-optmassmod').value;
      var maxfmod = document.getElementById('input-maxfuelmod').value;
      var massmod = document.getElementById('input-fsdmassmod').value;
      if (!fsd.match(/^[0-9][A-E]$/) || isNaN(mass) || isNaN(fuel) || isNaN(cargo) || !optmod.match(/^[-+0-9.]+%?$/) || !maxfmod.match(/^[-+0-9.]+%?$/) || !massmod.match(/^[-+0-9.]+%?$/))
      {
        alert("You must fill in all fields with appropriate values before submitting!");
        return;
      }
      var query = sprintf("%s,%f,%f,%d,%s,%s,%s", fsd, mass, fuel, cargo, encodeURIComponent(optmod), encodeURIComponent(maxfmod), encodeURIComponent(massmod));
      doXHR('jump_range', query, setJumpRange, failJumpRange);
    }

    function setJumpRange(data)
    {
      document.getElementById('output-jumprange-max').innerHTML = sprintf("%.2f Ly", data.max);
      document.getElementById('output-jumprange-full').innerHTML = sprintf("%.2f Ly", data.full);
      document.getElementById('output-jumprange-cargo').innerHTML = sprintf("%.2f Ly", data.laden);
      document.getElementById('output-jumprange').style.display = 'table-cell';
      document.getElementById('error-jumprange').style.display = 'none';
    }

    function failJumpRange(query, rcode)
    {
      document.getElementById('error-jumprange').innerHTML = sprintf('Could not calculate jump range from query.');
      document.getElementById('output-jumprange').style.display = 'none';
      document.getElementById('error-jumprange').style.display = 'table-cell';
    }
  </script>
</head>
<body>
<div class="wrap">
Simple jump range calculator powered by <a href="https://bitbucket.org/Esvandiary/edts">EDTS</a>.<br/><br/>

<table class="widget">
  <form onsubmit="doJumpRange(); return false;">
  <tr>
    <td class="wname">FSD:</td>
    <td class="winput"><input type="text" id="input-fsdclass" placeholder="FSD class, e.g. 6A" /></td>
  </tr>
  <tr>
    <td class="wname">Ship Mass:</td>
    <td class="winput"><input type="text" id="input-shipmass" placeholder="Ship mass in T, not including fuel" /></td>
  </tr>
  <tr>
    <td class="wname">Fuel Tank:</td>
    <td class="winput"><input type="text" id="input-fueltank" placeholder="Fuel tank size in T" /></td>
  </tr>
  <tr>
    <td class="wname">Cargo:</td>
    <td class="winput"><input type="text" id="input-cargo" placeholder="Cargo amount in T" /></td>
  </tr>
  <tr>
    <td class="wname">Optimal Mass:</td>
    <td class="winput"><input type="text" id="input-optmassmod" placeholder="In T or as a % boost" /></td>
  </tr>
  <tr>
    <td class="wname">Max Fuel Per Jump:</td>
    <td class="winput"><input type="text" id="input-maxfuelmod" placeholder="In T or as a % boost" /></td>
  </tr>
  <tr>
    <td class="wname">FSD Mass:</td>
    <td class="winput"><input type="text" id="input-fsdmassmod" placeholder="In T or as a % change" /></td>
  </tr>
  <tr>
    <td>&nbsp;<td/>
    <td><input type="submit" value="→" /></td></form>
  </tr>
  </form>
<tr><td class="woutput" id="output-jumprange" colspan="2" style="display: none">
  <table class="woutput-table" style="max-width: 500px"><tr><td>Max range:</td><td id="output-jumprange-max"></td></tr>
    <tr><td>Full-tank range:</td><td id="output-jumprange-full"></td></tr>
    <tr><td>Laden range:</td><td id="output-jumprange-cargo"></td></tr></table>
</td></tr>
<tr><td class="werror" id="error-jumprange" colspan="2" style="display: none"></td></tr></table>

</div>
</body>
</html>
