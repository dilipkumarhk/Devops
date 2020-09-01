import requests
import json
import urllib.parse
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import time
import sys

s = requests.Session()
s.proxies = {
  'http': 'http://proxy.us.dell.com:80',
  'https': 'http://proxy.us.dell.com:80',
}

def new_relic_data(nr_app_id,nr_app_name,nr_API_Key,nr_Insight_Key,account_id):
    headers = {
        'X-Api-Key': str(nr_API_Key),
        'Accept':'application/json, text/javascript, */*; q=0.01',
        'Content-Type':'application/json',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Origin': 'https://rpm.newrelic.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'Host': 'api.newrelic.com'
    }
    time.sleep(10)
    s1 = str(nr_app_id)
    acc_id = str(account_id)
    response = s.get('https://api.newrelic.com/v2/applications/'+s1+'/metrics/data.json?names%5B%5D=CPU%2FUser+Time&names%5B%5D%3DMemory%2FPhysical&summarize=true&raw=true', headers=headers)
    nr_json = json.loads(response.text)
    print(nr_json)
    for result in nr_json:
        met_data = nr_json['metric_data']
        metric = met_data['metrics']
        time_slice = metric[0]
        value = time_slice['timeslices']
        perc_cpu = value[0]['values']
        print("Average CPU Utilization: "+str(perc_cpu['percent'])+" %")
        time_slice2 = metric[1]
        value = time_slice2['timeslices']
        mem = value[0]['values']
        print("Total Used Memory: "+str(mem['used_mb_by_host'])+" MB")
        x_cpu = str(perc_cpu['percent'])
        y_mem = str(mem['used_mb_by_host'])

    time.sleep(10)

    response = s.get('https://api.newrelic.com/v2/applications/'+s1+'/metrics/data.json?names%5B%5D=CPU%2FUser%20Time&summarize=false&raw=true', headers=headers)
    nr_json = json.loads(response.text)
    for result in nr_json:
        met_data = nr_json['metric_data']
        metric = met_data['metrics']
        time_slice = metric[0]
        value = time_slice['timeslices']

    average_cpu=[]
    time_slice=[]
    count=1
    for data in value:
        time_data = data['values']
        avg_cpu = time_data['percent']
        average_cpu.append(avg_cpu)
        time_slice.append(count)
        count=count+1
    count = 0
    d = {'Average_CPU':average_cpu,'Time_Period':time_slice}
    df1 = DataFrame(d,columns=['Average_CPU','Time_Period'])
    #fig = df.plot(x='Time_Period', y='Average_CPU').get_figure()
    #fig.savefig('CPU_Utilization.pdf')
    time.sleep(10)

    response = s.get('https://api.newrelic.com/v2/applications/'+s1+'/metrics/data.json?names%5B%5D=Memory%2FPhysical&summarize=false&raw=true', headers=headers)
    nr_json = json.loads(response.text)
    for result in nr_json:
        met_data = nr_json['metric_data']
        metric = met_data['metrics']
        time_slice = metric[0]
        value = time_slice['timeslices']

    average_mem=[]
    time_slice2=[]
    count=1
    for data in value:
        time_data = data['values']
        avg_mem = time_data['used_mb_by_host']
        average_mem.append(avg_mem)
        time_slice2.append(count)
        count=count+1
    count = 0
    d2 = {'Average_Memory':average_mem,'Time_Period2':time_slice2}
    df2 = DataFrame(d2,columns=['Average_Memory','Time_Period2'])

    url = "https://insights-api.newrelic.com/v1/accounts/"+acc_id+"/query?nrql=SELECT%20average(apm.service.transaction.duration)%2Caverage(apm.service.transaction.external.duration)%20FROM%20Metric%20TIMESERIES%20LIMIT%20MAX%20since%201%20hour%20ago%20EXTRAPOLATE%20where%20appId%3D%27"+s1+"%27"

    payload = {}
    headers = {
        'Accept': 'application/json',
        'X-Query-Key': str(nr_Insight_Key)
    }

    response = s.request("GET", url, headers=headers, data=payload)
    rt_data = json.loads(response.text.encode('utf8'))

    average_web = []
    average_ext = []
    time_slice4 = []
    count = 1

    for result in rt_data:
        web_data = rt_data['timeSeries']
        for resp in web_data:
            avg_json = resp['results']
            if (avg_json[0]['average'] == 'None') and (avg_json[1]['average'] == 'None'):
                average_web.append(0)
                average_ext.append(0)
                count = count + 1
                time_slice4.append(count)
            else:
                average_web.append(avg_json[0]['average'])
                average_ext.append(avg_json[1]['average'])
                count = count + 1
                time_slice4.append(count)
        count = 0

    url = "https://insights-api.newrelic.com/v1/accounts/"+acc_id+"/query?nrql=SELECT%20max(apm.service.transaction.duration)%20from%20Metric%20TIMESERIES%20since%201%20hour%20ago%20EXTRAPOLATE%20FACET%20transactionName%20LIMIT%204%20where%20appId%3D%27"+s1+"%27"

    payload = {}
    headers = {
        'Accept': 'application/json',
        'X-Query-Key': '1BmIILa1ovsK_KIQ0skHemXq4GalXifV'
    }

    response = s.request("GET", url, headers=headers, data=payload)
    rt_data = json.loads(response.text.encode('utf8'))
    #print(rt_data)

    for result in rt_data:
        web_data = rt_data['facets']
    flag = 1
    if len(web_data) == 0:
        flag = 0
    elif len(web_data) == 1:
        max_resp = web_data[0]
    elif len(web_data) == 2:
        max_resp = web_data[0]
        max_resp2 = web_data[1]
    elif len(web_data) == 3:
        max_resp = web_data[0]
        max_resp2 = web_data[1]
        max_resp3 = web_data[2]
    elif len(web_data) == 4:
        max_resp = web_data[0]
        max_resp2 = web_data[1]
        max_resp3 = web_data[2]
        max_resp4 = web_data[3]

    if len(web_data) >= 1:
        url_trace = []
        max_url1 = []
        time_slice3 = []
        resp = {}
        count = 0
        for result in max_resp:
            time_data = max_resp['timeSeries']
            str1 = max_resp['name']
            if (len(str1) > 60):
                url_trace.append(str1[50:])
            else:
                url_trace.append(max_resp['name'])
            for result in time_data:
                resp = time_data[count]['results']
                res = [sub['max'] for sub in resp]
                max_url1.append(round(res[0], 2))
                time_slice3.append(count)
                count = count + 1
            count = 0
            break
    if len(web_data) >= 2:
        max_url2 = []
        for result in max_resp2:
            time_data = max_resp2['timeSeries']
            str1 = max_resp2['name']
            if (len(str1) > 60):
                url_trace.append(str1[50:])
            else:
                url_trace.append(max_resp2['name'])
            for result in time_data:
                resp = time_data[count]['results']
                res = [sub['max'] for sub in resp]
                max_url2.append(round(res[0], 2))
                count = count + 1
            count = 0
            break
    if len(web_data) >= 3:
        max_url3 = []
        for result in max_resp3:
            time_data = max_resp3['timeSeries']
            str1 = max_resp3['name']
            if (len(str1) > 60):
                url_trace.append(str1[50:])
            else:
                url_trace.append(max_resp3['name'])
            for result in time_data:
                resp = time_data[count]['results']
                res = [sub['max'] for sub in resp]
                max_url3.append(round(res[0], 2))
                count = count + 1
            count = 0
            break

    if len(web_data) >= 4:
        max_url4 = []
        for result in max_resp4:
            time_data = max_resp4['timeSeries']
            str1 = max_resp4['name']
            if (len(str1) > 60):
                url_trace.append(str1[50:])
            else:
                url_trace.append(max_resp4['name'])
            for result in time_data:
                resp = time_data[count]['results']
                res = [sub['max'] for sub in resp]
                max_url4.append(round(res[0], 2))
                count = count + 1
            count = 0
            break

    with PdfPages(r'New_Relic_Report_{}.pdf'.format(nr_app_name)) as export_pdf:

        plt.plot(df1['Time_Period'],df1['Average_CPU'],  color='green', marker='o')
        plt.title('Average CPU Utilization', fontsize=10)
        plt.xlabel('Time(Minutes)', fontsize=8)
        plt.ylabel('CPU Utilization', fontsize=8)
        plt.grid(True)
        export_pdf.savefig()
        plt.close()

        plt.plot(df2['Time_Period2'],df2['Average_Memory'], color='blue', marker='o')
        plt.title('Average Memory Utilization', fontsize=10)
        plt.xlabel('Time(Minutes)', fontsize=8)
        plt.ylabel('Memory Utilization', fontsize=8)
        plt.grid(True)
        export_pdf.savefig()
        plt.close()

        plt.plot(time_slice4, average_web,color='blue')
        plt.plot(time_slice4, average_ext,color='brown')
        plt.title('Web Vs External Transaction Time', fontsize=10)
        plt.legend(['Web Transaction Time(sec)', 'External Transaction Time(sec)'])
        plt.xlabel('Time(Minutes)', fontsize=8)
        plt.ylabel('Response Time (sec)', fontsize=8)
        plt.grid(True)
        export_pdf.savefig()
        plt.close()

        if flag > 0:
            if len(web_data) == 1:
                plt.plot(time_slice3, max_url1, color='blue')
                plt.legend([url_trace[0]], loc='upper right',fontsize='xx-small')
            elif len(web_data) == 2:
                plt.plot(time_slice3, max_url1, color='blue')
                plt.plot(time_slice3, max_url2, color='red')
                plt.legend([url_trace[0], url_trace[1]], loc='upper right',fontsize='xx-small')
            elif len(web_data) == 3:
                plt.plot(time_slice3, max_url1, color='blue')
                plt.plot(time_slice3, max_url2, color='red')
                plt.plot(time_slice3, max_url3, color='cyan')
                plt.legend([url_trace[0], url_trace[1], url_trace[2]], loc='upper right',fontsize='xx-small')
            elif len(web_data) == 4:
                plt.plot(time_slice3, max_url1, color='blue')
                plt.plot(time_slice3, max_url2, color='red')
                plt.plot(time_slice3, max_url3, color='cyan')
                plt.plot(time_slice3, max_url4, color='brown')
                plt.legend([url_trace[0], url_trace[1], url_trace[2], url_trace[3]], loc='upper right',fontsize='xx-small')
            plt.title('Top 4 Transaction Traces', fontsize=10)

            plt.xlabel('Time(Minutes)', fontsize=8)
            plt.ylabel('Response Time (sec)', fontsize=8)
            plt.grid(True)
            export_pdf.savefig()
            plt.close()

    return(x_cpu, y_mem)

if __name__ == '__main__':
    # Call main method of New Relic Data Generation
    new_relic_data(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
    #new_relic_data("533512949,405757336")