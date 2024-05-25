import niquests, re, io, json, time, sys, configparser

from lxml import etree
from datetime import datetime, timedelta

# retrieve today's date then minus one day as publish date will be GMT-7; adjust based on your local time.
todaydate = datetime.today() - timedelta(days=1)

# checks if today for any latest build releases; got new release return True else return False
def release_date_check():

    # setup date format to match release date format
    pre_date = todaydate.strftime('%e %b %Y')
    
    # send client side HTTP header range option to request server only send interested bytes range; adjust based on Channel section.
    headers = {'Range': 'bytes=1-418'}
    # send HTTP GET request with URL and headers
    r = niquests.get('https://support.fortinet.com/rss/firmware.xml', headers=headers, timeout=120, retries=5)
    
    # iterate mem loaded data (byte size 418) 
    for line in io.StringIO(r.text):
        # check if line contain "lastBuildDate"
        resultss = re.search(r'lastBuildDate', line)
        # due to empty match regex will return None, reverse check the regex search result
        if resultss != None:
            # remove new line
            one_line = line.replace("\n", "")
            # check if lastBuildDate equal to today's date
            if pre_date.lstrip() == " ".join(one_line.split(' ')[1:4]):
                return True
            else:
                return False

def download_xml_file():
    
    # open/download xml file
    # download xml file from web URL
    r = niquests.get('https://support.fortinet.com/rss/firmware.xml', stream=True)

    # create and open file as write with binary mode
    with open('rss_files/firmware.xml', 'wb') as fd:
        for chunk in r.iter_content():
            # save with filename "firmware.xml" under rss_file folder
            fd.write(chunk)

def get_today_released_firmware():
    
    # initiate empty list for matched group
    recordhit = []

    # setup date format to match release date format
    pre_date = todaydate.strftime('%e %b')
    
    fdx = etree.parse ('rss_files/firmware.xml', etree.XMLParser())
    # setup search path with "item"
    itemtitle = fdx.xpath(".//item")
    
    # iterate through 20 xml group to check if date matched 
    for u in range(0,20):

        myset = etree.tostring(itemtitle[u], pretty_print=True).decode()

        if re.search(pre_date, myset):
            # record match index number
            recordhit.append(u)
        else:
            continue
    
    # return matched group list    
    return recordhit
    

# extract released product firmware title 
def extract_release_info():
    
    # initiate empty list for product items
    k_release_info = []
    
    # parse xml file
    fdx = etree.parse ('rss_files/firmware.xml', etree.XMLParser())
    # setup search path with "item"
    itemtitle = fdx.xpath(".//item")

    # extract child group as string format
    for i in get_today_released_firmware():
        myset = etree.tostring(itemtitle[i], pretty_print=True).decode()
        
        # find product title for each released product 
        k_myset = re.findall(r'^<title>.*<\/title>$', myset, re.M)
        
        # replace HTML tag from product title
        pk_myset = re.sub(r'<title>|<\/title>', '', k_myset[0])
        
        # append each released product items into prep list
        k_release_info.append(pk_myset)

    # return captured product items as list
    return k_release_info

    
def sent_weebhook_notification():
    
    # load secret config ini file
    config = configparser.ConfigParser()
    config.read('config/mysecret.ini')
    
    # setup respective webhook teams channel link
    fml_webhook_url = config['webhook.prod.url'][fml_webhook_url]
    # forticlient webhook url
    fct_ems_webhook_url = config['webhook.prod.url'][fct_ems_webhook_url]
    # Fortiweb webhook url
    fwb_webhook_url = config['webhook.prod.url'][fwb_webhook_url]
    # fortimanager webhook url
    fmg_webhook_url = config['webhook.prod.url'][fmg_webhook_url]
    # fortisiem webhook url
    siem_webhook_url = config['webhook.prod.url'][siem_webhook_url]
    
    # setup HTTP header json data type
    heasders = {"content-type": 'application/json'}
    
    # if title match condition; send respective webhook message 
    for prod in extract_release_info():
        
        # setup filters to match respective products
        if re.match(r'FortiADC|FortiWeb|FortiDDoS', prod):
            
            # convert dict into json format with json.dumps
            mydata = {'text': prod + ' released'}
            send_post_webhook = niquests.post(fwb_webhook_url, data=json.dumps(mydata), headers=heasders, timeout=150)
        # setup filters to match respective products  
        elif re.match(r'FortiManager|FortiAnalyzer|FortiPortal|FortiOS', prod):
            
            # convert dict into json format with json.dumps
            mydata = {'text': prod + ' released'}
            send_post_webhook = niquests.post(fmg_webhook_url, data=json.dumps(mydata), headers=heasders, timeout=150)  
        # setup filters to match respective products     
        elif re.match(r'FortiSIEM|FortiSOAR', prod):
            
            # convert dict into json format with json.dumps
            mydata = {'text': prod + ' released'}
            send_post_webhook = niquests.post(siem_webhook_url, data=json.dumps(mydata), headers=heasders, timeout=150)
        # setup filters to match respective products
        elif re.match(r'FortiMail|FortiNDR|FortiCamera|FortiVoice|FortiSandbox|FortiFone', prod):
            
            # convert dict into json format with json.dumps
            mydata = {'text': prod + ' released'}
            send_post_webhook = niquests.post(fml_webhook_url, data=json.dumps(mydata), headers=heasders, timeout=150)
        # setup filters to match respective products
        elif re.match(r'FortiClient', prod):
            
            # convert dict into json format with json.dumps
            mydata = {'text': prod + ' released'}
            send_post_webhook = niquests.post(fct_ems_webhook_url, data=json.dumps(mydata), headers=heasders, timeout=150)
        
        # capture non-matched prod    
        else:
            mydata = {'text': prod + ' released'}
            send_post_webhook = niquests.post(fwb_webhook_url, data=json.dumps(mydata), headers=heasders, timeout=150)
        
    # return HTTP webhook respond code
    return send_post_webhook.text   



def main():
    
    # get today's date and time while script is ran
    localtoday = datetime.today()
    mytoday = localtoday.strftime('%d-%m-%Y %H:%M:%S.%f')
    mytext = ['released on', mytoday]
    
    # check if today's got any firmware release via RSS; if its return True means got update.
    if release_date_check() == True:
        
        
        # initiate download fresh copy of rss xml file
        download_xml_file()
        
        # pause 1 second
        time.sleep(1)
        
        # sent webhook notification messages
        sent_weebhook_notification()
        
        # pause 1 second
        time.sleep(1)
        
        # output product name and date
        # sample output: FortiAP-U 7.0.3, FortiWeb 7.4.3 released on 2024-04-10 10:39:10.573758
        print(*extract_release_info(), sep=', ', end=' ')
        print(*mytext, sep=' ')
        # exit program
        sys.exit(0)
    
    # if today no release update, exit program without download copy of XML file.     
    else:
        # no new release detected today; exit program to save resource
        # sample output: no release update - 10-04-2024 11:20:49.296881
        print(f'no release update - {mytoday}')
        sys.exit(1)

if __name__=="__main__":
    main()