import os
import subprocess,sys
import smtplib
import requests
import json
from datetime import datetime,timedelta
import time
import shutil
import numpy as np
import pandas as pd
from astropy.table import QTable, Table, Column
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.charset import Charset, BASE64
from email.mime.base import MIMEBase
from email import encoders
from email import charset
import glob
from NewRelic_Metrics import new_relic_data



def send_email(project_name,from_email,destro,nr_id,nr_API_Key,nr_Insight_Key,account_id):
	# defining the api-endpoint 
	url = "http://neoloadweb-api.np.perf.us.dell.com/v1/tests?status=TERMINATED&project="+project_name+"&limit=1&offset=0&sort=-startDate&pretty=true"
	headers = {'accept': 'application/json','accountToken': 'CSlF1F8zGNs61DZHPTSKVAdS'}

	r = requests.get(url,headers=headers)
	print(r.text)
	result_json = json.loads(r.text)

	txn_ids = []
	txn_names = []
	resp_dict = {}
	resp_values = []
	min_values = []
	max_values = []
	total_hits = []
	success = []
	failure = []
	resp_90 = []

	for result in result_json:
		test_id = result['id']
		txn_url = "http://neoloadweb-api.np.perf.us.dell.com/v1/tests/"+ test_id + "/elements?category=TRANSACTION"
		r_txn = requests.get(txn_url,headers=headers)
		#print(r_txn.text)
		result_json_txn = json.loads(r_txn.text)
		for tx_id in result_json_txn:
			txn_ids.append(tx_id['id'])
			txn_names.append(tx_id['name'])
		for id in txn_ids:
			resp_url = "http://neoloadweb-api.np.perf.us.dell.com/v1/tests/"+test_id+"/elements/"+id+"/values"
			r_resp = requests.get(resp_url,headers=headers)
			resp_dict = json.loads(r_resp.text)
			resp_values.append(round((resp_dict['avgDuration']/1000),2))
			min_values.append(round((resp_dict['minDuration']/1000),2))
			max_values.append(round((resp_dict['maxDuration']/1000),2))
			total_hits.append(resp_dict['count'])
			success.append(resp_dict['successCount'])
			failure.append(resp_dict['failureCount'])
			perc_url = "http://neoloadweb-api.np.perf.us.dell.com/v1/tests/"+test_id+"/elements/"+id+"/percentiles"
			perc_resp = requests.get(perc_url,headers=headers)
			perc_dict = json.loads(perc_resp.text)
			r_90 = perc_dict[899]['duration']
			resp_90.append(round((r_90/1000),2))
			
		body = "Test Summary of Latest Build - {}\n\n".format(project_name) + "Run Name: " + result['name'] + '\n' + "Project: " + result['project'] + '\n' + "Scenario: " + result['scenario'] + '\n' + "Quality Status: " + result['qualityStatus'] + '\n'
		time1 = int(result['startDate'])/1000
		start_time = datetime.utcfromtimestamp(time1).strftime('%Y-%m-%d') + time.strftime("%H:%M", time.localtime(time1)) + " CST"
		time2 = int(result['endDate'])/1000
		end_time = datetime.utcfromtimestamp(time1).strftime('%Y-%m-%d') + time.strftime("%H:%M", time.localtime(time2)) + " CST"
		test_dur = round(int(result['duration'])/1000/60,2)
		dur = str(test_dur)
		body = body + "Test Start Time: " + start_time + "\n" + "Test End Time: " + end_time + "\n" + "Test Duration: " + dur + " minutes"
	nr_data = []
	time.sleep(10)
	nr_app_list = {}
	nr_app_list = eval(nr_id)
	nr_app_id = nr_app_list.keys()
	nr_app_name = nr_app_list.values()
	print(nr_app_id)
	print(nr_app_name)
	for id,name in zip(nr_app_id,nr_app_name):
		nr_data = new_relic_data(id,name,nr_API_Key,nr_Insight_Key,account_id)
		app_name = nr_app_list[id]
		body = body + "\n\n" + "NewRelic Data for Application - {}:\n\n".format(app_name) + "Average CPU Utilization during the test: " + nr_data[0] + " %"
		body = body + "\n\n" + "Average Memory Utilization during the test: " + nr_data[1] + " MB"

	body = body + "\n\n" + "Find the attached pdf for detailed New Relic Metrics!"
	body = body + "\n\n" + "Find the attached html file for detailed Response Time Summary"
	body = body + "\n\n" + "Also, find the attached image for average response time graph!"
	body = body + "\n\n\n" + "Regards," + "\n" + "E-Support QA Perf Team"

	data = np.zeros(len(resp_values), dtype={'names':('Transaction_Name','Minimum','Average','Maximum','90th Percentile','Total Hits','Pass','Fail'),'formats':('U30','f8','f8','f8','f8','i4','i4','i4')})       
	data['Transaction_Name'] = txn_names
	data['Minimum'] = min_values
	data['Average'] = resp_values
	data['Maximum'] = max_values
	data['90th Percentile'] = resp_90
	data['Total Hits'] = total_hits
	data['Pass'] = success
	data['Fail'] = failure


	t = Table([txn_names,min_values,resp_values,max_values,resp_90,total_hits,success,failure],names=('Transaction_Name', 'Minimum','Average','Maximum','90th Percentile','Total Hits','Pass','Fail')) 
	t.write('RT_Summary.html', format='jsviewer')

	#Average Response Time Graph
	url2 = "http://neoloadweb-api.np.perf.us.dell.com/v1/tests/"+test_id+"/graph"

	data = {
	  "width": 900,
	  "height": 500,
	  "title": "Average Response Time Graph",
	  "rasterType": "PNG",
	  "xAxisLabel": "X Axis",
	  "yAxisLabel": "Y Axis",
	  "legend": "true",
	  "multiYAxis": "true",
	  "theme": "DARK",
	  "elementIds": [
		{
		  "id": "all-requests",
		  "statistics": [
			"AVG_DURATION"
		  ]
		}
	  ],
	  "counterIds": [
		"a4bed45a-06b2-48e1-94fd-3ea979e4f360",
		"b5be82ff-3563-4812-93a5-4ea888e4e254"
	  ]
	}
	header2 = {'accept': 'image/png','accountToken': 'CSlF1F8zGNs61DZHPTSKVAdS','Content-Type': 'application/json'}
	img_resp = requests.post(url2, data=json.dumps(data).encode('ascii'), headers=header2,stream=True)

	with open('avg_resp_time.jpg', 'wb') as out_file:
		shutil.copyfileobj(img_resp.raw, out_file)
	#del img_resp


	TO = destro
	SUBJECT = 'Latest Perf Test Results - {}'.format(project_name)
	TEXT = r.text
	exchange_sender = from_email

	print(TO)
	charset.add_charset('utf-8', charset.SHORTEST, charset.QP)
	full_email = MIMEMultipart('mixed')
	full_email["Subject"] = SUBJECT
	full_email["From"] = exchange_sender
	full_email["To"] = TO

	mail_body = MIMEMultipart('alternative')
	mail_body.attach(MIMEText((body + "\n\n").encode('utf-8'),'plain', _charset='utf-8'))

	#Adding response time table data to E-Mail
	report_file = open('RT_Summary.html')
	email_body = """<!DOCTYPE HTML>
					<html lang = "en">
						<head>
							<meta charset = "UTF-8" />
						</head>
						<body>
							<h1>Response Time Summary Table</h1>
							<legend>SLA Profile</legend>
							<p>
								<label>Define Response Time SLA in Seconds</label>
								<input type = "text"
								id = "SLA"
								value = "" />
							</p>
							<button type="submit" onclick="Apply_SLA()">Apply SLA</button>
						</body>
					</html>"""
	email_body += report_file.read()
	email_body = email_body + """<script>
		function Apply_SLA(){
		var trTags = document.getElementsByTagName("tr");
		var sla = parseFloat(document.getElementById("SLA").value)
		for (var i = 1; i < trTags.length; i++) {
		var tdFourthEl = trTags[i].getElementsByTagName("td")[4]; // starts with 0, so 3 is the 4th element
		var splitList = tdFourthEl.innerHTML.split(".")
		if(parseInt(splitList[1]) > 0)
		{
			var j = parseInt(splitList[0])+1
		}
		if (j > sla) {
			tdFourthEl.style.backgroundColor = "LIGHTCORAL";
		} else if (j <= sla) {
			tdFourthEl.style.backgroundColor = "LIME";
		}
		j=0
		}
		}
		</script>"""

	part = MIMEBase('application', "octet-stream")
	part.set_payload(email_body)
	encoders.encode_base64(part)
	part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename("RT_Summary.html"))
	full_email.attach(part)

	#mail_body.attach(MIMEText((email_body).encode('utf-8'),'html', _charset='utf-8'))
	full_email.attach(mail_body)

	#full_email.attach(MIMEText(open("New_Relic_Report.pdf").read()))
	parts = ['part2','part3','part4','part5','part6','part7']
	count = 0
	file_list = glob.glob('*.pdf')
	for f in file_list:
		filename = f  # In same directory as script

		# Open PDF file in binary mode
		with open(filename, "rb") as attachment:
			# Add file as application/octet-stream
			# Email client can usually download this automatically as attachment
			parts[count] = MIMEBase("application", "octet-stream")
			parts[count].set_payload(attachment.read())

		# Encode file in ASCII characters to send by email
		encoders.encode_base64(parts[count])

		# Add header as key/value pair to attachment part
		parts[count].add_header(
			"Content-Disposition",
			f"attachment; filename= {filename}",
		)

		# Add attachment to message and convert message to string
		full_email.attach(parts[count])


	# attach image to message body
	img_data = open('avg_resp_time.jpg', 'rb').read()
	image = MIMEImage(img_data, name=os.path.basename('avg_resp_time.jpg'))
	full_email.attach(image)


	server = smtplib.SMTP('smtp-out.us.dell.com', 25)
	server.ehlo()
	server.starttls()
	#server.login(exchange_sender, exchange_passwd)

	text_msg = full_email.as_string()
     #email_trigger(exchange_sender,TO, text_msg)
	try:
		server.sendmail(exchange_sender, TO.split(','), text_msg)
		#server.sendmail(sender,to.split(','), msg)
		print ('email sent')
	except:
		print ('error sending mail')

	server.quit()

	for f in file_list:
		os.remove(f)

if __name__ == "__main__": 
    send_email(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7])