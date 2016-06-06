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

    function doSectorPosition()
    {
      doXHR('sector_position', document.getElementById('input-sectorpos').value, setSectorPosition, failSectorPosition);
    }

    function doSystemPosition()
    {
      doXHR('system_position', document.getElementById('input-systempos').value, setSystemPosition, failSystemPosition);
    }

    function doSectorName()
    {
      var x = document.getElementById('input-sectorname-x').value;
      var y = document.getElementById('input-sectorname-y').value;
      var z = document.getElementById('input-sectorname-z').value;
      if (isNaN(x) || isNaN(y) || isNaN(z) || x.length === 0 || y.length === 0 || z.length === 0)
      {
        alert("You must fill in all fields with numeric values before submitting!");
        return;
      }
      var query = sprintf("%.6f,%.6f,%.6f", x, y, z);
      doXHR('sector_name', query, setSectorName, failSectorName);
    }

    function doSystemName()
    {
      var x = document.getElementById('input-systemname-x').value;
      var y = document.getElementById('input-systemname-y').value;
      var z = document.getElementById('input-systemname-z').value;
      var mcode = document.getElementById('input-systemname-m').value;
      console.log("x = " + typeof(x) + ", y = " + typeof(y) + ", z = " + typeof(z) + ", m = " + typeof(mcode));
      if (isNaN(x) || isNaN(y) || isNaN(z) || x.length === 0 || y.length === 0 || z.length === 0 || !mcode.match(/[a-h]/i))
      {
        alert("You must fill in all fields with appropriate values (numeric for X,Y,Z; a-h for mcode) before submitting!");
        return;
      }
      var query = sprintf("%.6f,%.6f,%.6f/%s", x, y, z, mcode);
      doXHR('system_name', query, setSystemName, failSystemName);
    }

    function setSectorPosition(data)
    {
      if (data.type === 'ha')
      {
        var pos = sprintf("Centre: [%.3f, %.3f, %.3f]", data.centre.x, data.centre.y, data.centre.z);
        var size = sprintf("Radius: %.2fLy", data.radius);
      }
      else
      {
        var pos = sprintf("Origin: [%.3f, %.3f, %.3f]", data.origin.x, data.origin.y, data.origin.z);
        var size = sprintf("Size: %dLy", data.size);
      }
      document.getElementById('output-sectorpos-name').innerHTML = "Name: " + data.name;
      document.getElementById('output-sectorpos-pos').innerHTML = pos;
      document.getElementById('output-sectorpos-size').innerHTML = size;
      document.getElementById('output-sectorpos-type').innerHTML = "Type: " + (data.type === 'ha' ? "Hand-Authored" : "Procedurally Generated");

      document.getElementById('error-sectorpos').innerHTML = "";
      document.getElementById('output-sectorpos').style.display = 'table-cell';
    }

    function setSystemPosition(data)
    {
      var pos = sprintf("Position: [%.3f, %.3f, %.3f] ± %dLy per axis", data.position.x, data.position.y, data.position.z, data.uncertainty);

      document.getElementById('output-systempos-name').innerHTML = "Name: " + data.name;
      document.getElementById('output-systempos-pos').innerHTML = pos;

      document.getElementById('error-systempos').innerHTML = "";
      document.getElementById('output-systempos').style.display = 'table-cell';
    }

    function setSectorName(data)
    {
      var pos = sprintf("Position: [%.3f, %.3f, %.3f]", data.position.x, data.position.y, data.position.z);
      var names = [];
      data.names.forEach(function(t) { names.push(t.name); });
      
      document.getElementById('output-sectorname-pos').innerHTML = pos;
      if (names.length > 1)
        document.getElementById('output-sectorname-name').innerHTML = "<div style='float:left'>Possible names:&nbsp;</div><div style='float:left'>" + names.join('<br/>') + "</div>";
      else if (names.length == 1)
        document.getElementById('output-sectorname-name').innerHTML = "Name: " + names[0];
      else
        document.getElementById('output-sectorname-name').innerHTML = "No names found";
    }

    function setSystemName(data)
    {
      console.log(data);
      var pos = sprintf("Position: [%.3f, %.3f, %.3f]", data.position.x, data.position.y, data.position.z);
      var names = [];
      data.names.forEach(function(t) { names.push(t.name + '?'); });
      
      document.getElementById('output-systemname-pos').innerHTML = pos;
      if (names.length > 1)
        document.getElementById('output-systemname-name').innerHTML = "<div style='float:left'>Possible names:&nbsp;</div><div style='float:left'>" + names.join('<br/>') + "</div>";
      else if (names.length == 1)
        document.getElementById('output-systemname-name').innerHTML = "Name: " + names[0];
      else
        document.getElementById('output-systemname-name').innerHTML = "No names found";
    }

    function failSectorPosition(query, rcode)
    {
      document.getElementById('output-sectorpos-name').innerHTML = "";
      document.getElementById('output-sectorpos-pos').innerHTML = "";
      document.getElementById('output-sectorpos-size').innerHTML = "";
      document.getElementById('output-sectorpos-type').innerHTML = "";
      document.getElementById('error-sectorpos').innerHTML = sprintf('Sector "%s" could not be located.', query);
    }

    function failSystemPosition(query, rcode)
    {
      document.getElementById('output-systempos-name').innerHTML = "";
      document.getElementById('output-systempos-pos').innerHTML = "";
      document.getElementById('error-systempos').innerHTML = sprintf('System "%s" could not be located.', query);
    }

    function failSectorName(query, rcode)
    {
      document.getElementById('output-sectorname-pos').innerHTML = "";
      document.getElementById('output-sectorname-name').innerHTML = "";
      document.getElementById('error-sectorname').innerHTML = sprintf('Could not find names for sector around [%s].', query);
    }

    function failSystemName(query, rcode)
    {
      document.getElementById('output-systemname-pos').innerHTML = "";
      document.getElementById('output-systemname-name').innerHTML = "";
      document.getElementById('error-systemname').innerHTML = sprintf('Could not find names for system around [%s].', query);
    }
  </script>
</head>
<body>
<div class="wrap">
Hello, friend! This is a simple demo of the procedurally-generated name magic.<br/>
There is also a <a href="/api/v1">barebones API</a> (which this demo uses) that you can query yourself.<br/>
Or, you could host/integrate it yourself by <a href="https://bitbucket.org/Esvandiary/edts/branch/feature/pgnames">grabbing it from BitBucket</a>.<br/>
Please don't spam this site too much, it's only a little babby server. :)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- CMDR Alot<br/><br/>

<table class="widget">
<tr>
  <td class="wname">Sector Position:</td>
  <form onsubmit="doSectorPosition(); return false;"><td class="winput"><input type="text" id="input-sectorpos" placeholder="Sector Name" /></td>
  <td><input type="submit" value="→" /></td></form>
</tr>
<tr><td class="woutput" id="output-sectorpos" colspan="3">
  <table class="woutput-table"><tr><td id="output-sectorpos-name"></td><td id="output-sectorpos-pos"></td></tr>
    <tr><td id="output-sectorpos-size"></td><td id="output-sectorpos-type"></td></tr></table>
</td></tr><tr><td class="werror" id="error-sectorpos" colspan="3"></td></tr></table>

<table class="widget">
<tr>
  <td class="wname">System Position:</td>
  <form onsubmit="doSystemPosition(); return false;"><td class="winput"><input type="text" id="input-systempos" placeholder="System Name" /></td>
  <td><input type="submit" value="→" /></td></form>
</tr>
<tr><td class="woutput" id="output-systempos" colspan="3">
  <table class="woutput-table"><tr><td id="output-systempos-name"></td></tr><tr><td id="output-systempos-pos"></td></tr></table>
</td></tr><tr><td class="werror" id="error-systempos" colspan="3"></td></tr></table>

<table class="widget">
<tr>
  <td class="wname">Sector Name:</td>
  <form onsubmit="doSectorName(); return false;">
    <td class="winput">[&nbsp;<input type="text" id="input-sectorname-x" placeholder="X" />&nbsp;,</td>
    <td class="winput"><input type="text" id="input-sectorname-y" placeholder="Y" />&nbsp;,</td>
    <td class="winput"><input type="text" id="input-sectorname-z" placeholder="Z" />&nbsp;]</td>
    <td><input type="submit" value="→" /></td></form>
  </form>
</tr>
<tr><td class="woutput" id="output-sectorname" colspan="5">
  <table class="woutput-table"><tr><td id="output-sectorname-pos"></td></tr>
    <tr><td id="output-sectorname-name"></td></tr></table>
</td></tr><tr><td class="werror" id="error-sectorname" colspan="5"></td></tr></table>

<table class="widget">
<tr>
  <td class="wname">System Name:</td>
  <form onsubmit="doSystemName(); return false;">
    <td class="winput">[&nbsp;<input type="text" id="input-systemname-x" placeholder="X" />&nbsp;,</td>
    <td class="winput"><input type="text" id="input-systemname-y" placeholder="Y" />&nbsp;,</td>
    <td class="winput"><input type="text" id="input-systemname-z" placeholder="Z" />&nbsp;]</td>
    <td class="winput"><input type="text" id="input-systemname-m" placeholder="mcode" /></td>
    <td><input type="submit" value="→" /></td></form>
  </form>
</tr>
<tr><td class="woutput" id="output-systemname" colspan="6">
  <table class="woutput-table"><tr><td id="output-systemname-pos"></td></tr>
    <tr><td id="output-systemname-name"></td></tr></table>
</td></tr><tr><td class="werror" id="error-systemname" colspan="6"></td></tr></table>
</div>
</body>
</html>
