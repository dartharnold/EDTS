<!DOCTYPE html>
<html>
<head>
  <title>PRETTY PICTURE MAKER</title>
  <script type="text/javascript">
    function doSubmit()
    {
      var txt = document.getElementById("systems").value;
      txt = txt.replace(/\r\n/g, ",").replace(/\n/g, ",");
      window.location = "/mkimg/" + txt;
    }
  </script>
</head>
<body>
SYSTEMS GO HERE<br/>
<textarea id="systems" name="systems" style="width:600px;height:800px"></textarea><br/><br/>
<button onclick="doSubmit()">MAKE PRETTY PICTURE</button>

</body>
</html>
