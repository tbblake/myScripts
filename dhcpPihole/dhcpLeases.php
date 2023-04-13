<?php
// https://github.com/tbblake/myScripts/tree/main/dhcpPihole
$htmlTable=array_key_exists("htmlTable",$_GET);
$textTable=array_key_exists("textTable",$_GET);
$noDate=array_key_exists("noDate",$_GET);
$dateFormat="m/d/y h:i:sa";

if($htmlTable || $textTable) {
	$file="/etc/pihole/dhcp.leases";
	$data=file($file);
	natsort($data);
	$data=array_reverse($data,false);
	$leases=[];
	foreach ($data as $line) {
		$lease=explode(" ",$line);
		array_pop($lease);
		array_push($lease,$lease[0]);
		array_push($lease,ip2long($lease[2]));
		$lease[0]=date($dateFormat,$lease[0]);
		array_push($leases,$lease);
	}
}
if($htmlTable) {
	if(!$noDate) {
		print("<table id='date'><tr><td>");
		print date($dateFormat);
		print("</td></tr></table><br>\n");
	}
	print("<table id='dhcp'>\n");
	print("<tr><th>Expires</th><th>MAC</th><th>IP</th><th>Name</th></tr>\n");
	foreach ($leases as $lease) {
		print("<tr>");
		print("<td>".$lease[0]."</td>");
		print("<td>".$lease[1]."</td>");
		print("<td>".$lease[2]."</td>");
		print("<td>".$lease[3]."</td>");
		print("</tr>\n");
	}
	print("</table>\n");
} elseif ($textTable) {
	if(!$noDate) {
		print(date($dateFormat)."\n\n");
	}
	$strLengths=array_fill(0,4,0);
	foreach ($leases as $lease) {
		for($i=0;$i<4;$i++) {
			if(strlen($lease[$i]) > $strLengths[$i]) {
				$strLengths[$i]=strlen($lease[$i]);
			}
		}
	}
	foreach ($leases as $lease) {
		for($i=0;$i<4;$i++) {
			$formatSpec="%-".$strLengths[$i]."s  ";
			printf($formatSpec,$lease[$i]);
		}
		print("\n");
	}
} else {
	?>
	<!doctype html>
	<html>
	<head>
	<title>Lease Status</title>
	<link href="data:image/x-icon;base64,AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbAAACnAUBJ98BAASnAAAAIwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAABxAAAC5DIEvf9FBP3/NwTP/wIACukAAAByAAAACgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABACAAm/IQKH/w4BSv8LAUP/HwKF/xMCWf8MAUX/IwKN/wMAF9EAAAAhAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGALAOt/0wF//8eAn3/HAJ6/zoE2P8kA5T/HgJ//0sE//81BMj/AQAEpwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA0j8E6v81BMv/BQEn/0ME9v9CBPX/RwT//xMCWv82BM3/RwT//wMBFN4AAAAAAAAAAAAAAAAAAAAAAAAARw4CSf8OAkz/AwEX/wUBJP8rA6b/QgT0/zMDxP8FAST/BQEp/x4CgP8LAUT9AAAAQwAAAAAAAAAAAAAAAAAAAaA9BOL/CgE//ykDo/9CBPX/JgOa/wUBKf8bAnP/PgTn/ywDrf8IATf/OwTc/wAAAZ0AAAAAAAAAAAAAAAAAAAGCMQO8/x0Cev8+BOT/QgTz/0ME+f8JATr/PATe/0IE9v9ABO7/IgOL/zMEw/8AAAGHAAAAAAAAAAAAAAAAAAAAFQMAFdMFASn/IwKO/0YE//88BOD/BAEd/zYEzf9HBP//KwOn/woBO/8EAR/aAAAAGwAAAAAAAAAAAAAAAAAAAAAAAABrJgOb/xsCdv8QAk//GgJw/xsCdf8hA4b/FgJl/yECh/8lA5j/AAAAZwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGwcANN83AM//DgBH/y8Ct/9LBP//OAPU/xQAWv81AMr/BgAt3gAAABYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAQC2AFEy/wRmTP8EBh7/DwBP/wQCHf8DWkX/AF81/wAEAMsAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB/AHA2/wDIWP8AulD/AFId/wAGAP8APAv/AK9M/wDJWf8AjEL/AQMCrQAAAAAAAAAAAAAAAAAAAAAAAAAKAR8K6QDCXP8Aq1H/AJBF/wC6V/8ANRf/ALBQ/wCVRP8Ao0z/AMle/wBAHf8AAAAkAAAAAAAAAAAAAAAAAAAAGAEkDv8AoEv/AKlQ/wCvUf8AdDb/AAIBvwBcKf8ArFD/AKtR/wClT/8AQR7/AAAAPAAAAAAAAAAAAAAAAAAAAAIAAABSAQICngISBtMBBwS6AAAAbwAAAAQAAABXAQQDsQITB9MBBAOrAAAAZAAAAAkAAAAA/j8AAPwfAADwBwAA4AMAAOADAADgAwAAwAEAAMABAADgAwAA8AcAAPAHAADwBwAA8AMAAOADAADgAwAA8ccAAA==" rel="icon" type="image/x-icon" />
	<script>
		let updateTimeSeconds=5;
		let updateTime=updateTimeSeconds*1000;
		setInterval(updateStatus,updateTime);
		function updateStatus() {
			var xhttp = new XMLHttpRequest();
			xhttp.onreadystatechange = function() {
				if (this.readyState == 4 && this.status == 200) {
					document.getElementById("status").innerHTML = this.responseText;
				}
			};
			xhttp.open("GET", "dhcpLeases.php?htmlTable", true);
			xhttp.send();
		}
		updateStatus();
	</script>
	<style>
	#dhcp {
		font-family: monospace;
		border-collapse: collapse;
	}

	#dhcp td, #dhcp th {
		border: 0px;
		padding: 0 5px;
	}

	#dhcp tr:nth-child(even){background-color: #f2f2f2;}

	#dhcp tr:hover {background-color: #ddd;}

	#dhcp th {
		text-align: left;
		background-color: #444444;
		color: white;
	}

	#date {
		font-family: monospace;
		border-collapse: collapse;
		border: 0px;
		padding: 0 5px;
	}

	</style>
	</head>
	<body>
	<div id="status">
	</body>
	</html>
	<?php
}
?>
