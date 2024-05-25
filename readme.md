# Automate RSS update with filter conditional trigger WebHook sent notification into Teams Channel(s)

Objective to achieve were to save the time for admin and technical personal to check RSS feed aggregators.
This program were not meant to cover all use cases. However, serve as a start with fundamental approach to automate the process. 

See script automation with CRON in action:
[![image](https://github.com/scheehan/rss_update_teams_webhook/blob/master/Images/intro.png)](https://youtu.be/vozB2PYIV6g)

## Source of RSS information  

### RSS/Atom XML format file - firmware update
 
Here is an example RSS priodically update for fimware release  
This serve as an example, RSS xml file can come from any provider, as long as follow RSS/ATOM namaspace format. 

> https://support.fortinet.com/rss/firmware.xml

![Automate python script with CRON job standard output and standard error redirection](https://github.com/scheehan/rss_update_teams_webhook/blob/master/Images/rss_ns_channel.png)

### What is RSS in generally.

What is [RSS][1] (RDF (Resource Description Framework) Site Summary or Really Simple Syndication). To put into simple term, RSS is a dialect of XML. All RSS files must conform to the XML 1.0 specification, as published on the World Wide Web Consortium (W3C) website.

web feed that allows users and applications to access updates to websites in a standardized, computer-readable format. Subscribing to RSS feeds can allow a user to keep track of many different websites in a single news aggregator, which constantly monitor sites for new content, removing the need for the user to manually check them. 
 
Websites usually use RSS feeds to publish frequently updated information, such as blog entries, news headlines, episodes of audio and video series, or for distributing podcasts. An RSS document (called "feed", "web feed", or "channel") includes full or summarized text, and metadata, like publishing date and author's name. RSS formats are specified using a generic XML file.

These features and functions allow automation possible due to machine-readable information metadata feeds to be process and handle information greater efficiency and certainty.

## Understand RSS XML structure

In order to work with RSS feed metadata. we need to understand have a bit of unerstanding how RSS XML structure constructed. 

At the top level, a RSS document is a \<rss\> element, with a mandatory attribute called version, that specifies the version of RSS that the document conforms to. If it conforms to this specification, the version attribute must be 2.0.

Subordinate to the \<rss\> element is a single \<channel\> element, which contains information about the channel (metadata) and its contents.

### Understand RSS namespace  

[XML namespaces][3] provide a simple method for qualifying element and attribute names used in Extensible Markup Language documents by associating them with namespaces identified by URI references.

Generally common available namespace provided by W3C were sufficient to common use cases. namespace topic were beyond the scope of this article. if you interested to know more.

More info can be found in below articles.

> https://www.disobey.com/detergent/2002/extendingrss2/  
> https://validator.w3.org/feed/docs/howto/declare_namespaces.html


### Python Modules to parse XML 
- atoma
- [lxml][2]
- [ElementTree][4] 
- minidom

Tried with some others XML parser stated above. I end up with [lxml][2] as its  compatible with well-known ElementTree API, and documentation seem cover most of common use cases. Additionally, lxml support xpath() method.

code snippets example usage for atoma and lxml for comparison.

```python
mylist = [0,1,3]

afeed = atoma.parse_rss_file('rss_files/firmware.xml')

efdx = etree.parse('rss_files/firmware.xml', etree.XMLParser())
itemtitle = efdx.xpath(".//item")

def lxmlreleaseprod(j):
    myklist = []
    
    for i in j:
        myset = etree.tostring(itemtitle[i], pretty_print=True).decode()
        k_myset = re.findall(r'^<title>.*<\/title>$', myset, re.M)
        pk_myset = re.sub(r'<title>|<\/title>', '', k_myset[0])
        myklist.append(pk_myset)
        
    return myklist
    
def atomareleasedprod(k):
    myklist = []

    for i in k:
        myklist.append(afeed.items[i].title)

    return myklist

print(*lxmlreleaseprod(mylist), sep=', ', end=' ')
print(*m, sep=' ')
print(*atomareleasedprod(mylist), sep=', ', end=' ')    
print(*l, sep=' ')
```

Output:
> FortiSOAR 7.5.0, FortiAP-W2 7.2.4, FortiPAM 1.3.0 lxml 2024-04-10 18:00:03.717363  
> FortiSOAR 7.5.0, FortiAP-W2 7.2.4, FortiPAM 1.3.0 atoma 2024-04-10 18:00:03.717363

---

## Put all together to work
### pseudo code

1. pull latest feeds xml as memory
2. locate today's latest build release date <lastBuildDate> vs local today's date - 1 day (GMT -7)
3. comparison checks; if latest build release date same as today's date, means there were new releases; if latest build release date not the same as today's date, means no new releases as of today.
4. checks return False;stop further process
5. wait for next schedule; 24 hours; 7:59am GMT+8
6. checks return True; proceed download latest copy of XML file
7. parse XML file metadata content
8. perform checks and title metadata extraction
9. complile metadata into JSON format, and sent via webhook url



### Perform release date checks

load rss xml file into memory with niquests. limit bytes range to be pull from rss url top level \<rss\> and \<channel\> elements without \<items\> contents.

```python
    pre_date = todaydate.strftime('%e %b %Y')
    
    # send client side HTTP header range option to request server only send interested bytes range; adjust based on Channel section.
    headers = {'Range': 'bytes=1-418'}
    # send HTTP GET request with URL and headers
    r = niquests.get('https://support.fortinet.com/rss/firmware.xml', headers=headers)
    
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
```

### perform extraction on which product releases firmware version

isolated releases for the day. perform extraction on each product \<title\> metadata add into list for further process later

```python
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
```

XML \<item\> content

![image](https://github.com/scheehan/rss_update_teams_webhook/blob/master/Images/rss_childs.png)

### identify each product to be sent via webhook to respective teams channel

Some security measure by moving webhook url into separate ini config, and include into .gitignore file.
more into about [configparser][5].

These steps were to encourage you to practise basic security measure, merely to demontrate way to separate secret info. uses configparser is just one of the methods.

Here is a discussion about that topic.  
storing-the-secrets-passwords-in-a-separate-file  
> https://stackoverflow.com/questions/25501403/storing-the-secrets-passwords-in-a-separate-file

```python
[webhook.prod.url]
# forticlient webhook url
fct_ems_webhook_url = 'https://example.webhook.office.com/webhookb2/<hash-key>/IncomingWebhook/<hash-key>'

```

Perform regex match to capture respective product name. Follow by, converting captured data into JSON format as python dict data type does not equal to json string type, necessary format dict data type into json (string) type with json.dumps(). if you need to load json into python as dict, uses json module load function json.loads(). once data prep with JSON type, important text message can be sent via webhook into respective Teams Channel.

JSON strings always support unicode

|JSON|Python|
|--  |--    |
|string	| string *1   |
|number | int/float *2|
|object | dict        |
|array  | list        |
|boolean| bool        |
|null   | None        |

one of the challenges encounter during testing phase were, conneciton sometime may gets timeout or unreachable to Teams WebHook server. solution to counter the timeout issue were to add [timeout][7] options to give it more time before actual timeout expired.

### Exception Message:
> exceptions.ConnectTimeout


```python
config = configparser.ConfigParser()
    config.read('config/mysecret.ini')
    
    # setup respective webhook teams channel link
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
        
        # setup filters to match respective products; add timeout to handle slow server response
        if re.match(r'FortiADC|FortiWeb|FortiDDoS', prod):
            
            # convert dict into json format with json.dumps
            mydata = {'text': prod + ' released'}
            send_post_webhook = niquests.post(fwb_webhook_url, data=json.dumps(mydata), headers=heasders, timeout=150)
```

### Final step to complete the prcess with Linux CRON scehduler to invoke script.

There were discussion about whether uses python scheduler or system scheduler. Here is the topic for the discussion should which approach suitable for your use case.
> https://stackoverflow.com/questions/31189783/schedule-time-and-date-to-run-script  
> https://stackoverflow.com/questions/68862565/running-scheduled-task-in-python

For this particular example, i uses linux cron as scheduler

![image](https://github.com/scheehan/rss_update_teams_webhook/blob/master/Images/crontab_editor.png)

webhook_output.log logging output example

> no release update - 2024-04-08 09:00:01.412303  
> no release update - 2024-04-09 09:00:01.936488  
> FortiAP-U 7.0.3, FortiWeb 7.4.3 released on 2024-04-10 10:39:10.573758

---

## The result

![image](https://github.com/scheehan/rss_update_teams_webhook/blob/master/Images/incoming_teams_webhook.png)

Here is the guide how to enable Teams Channel [webhook][6]

---

## Activate virtual environment
```
python -m venv .venv

Windows:
.\.venv\Scripts\activate

Linux & Unix:
source .venv/bin/activate

pip install -r requirements.txt
```

## Installation
```
git clone https://github.com/scheehan/rss_update_teams_webhook
cd rss_update_teams_webhook

crontab -e
59 7 * * * /usr/bin/python /var/automation/rss_update_teams_webhook/rss_tracker_with_webhook.py >> /tmp/webhook_output.log 2>&1

```



[1]: https://www.rssboard.org/rss-specification/ 'Latest RSS specification'
[2]: https://lxml.de/ 'lxml XML toolkit'
[3]: https://www.w3.org/TR/REC-xml-names/ 'Namespaces in XML'
[4]: https://docs.python.org/3/library/xml.etree.elementtree.html#module-xml.etree.ElementTree/ 'The ElementTree XML API'
[5]: https://docs.python.org/3/library/configparser.html/ 'Configuration file parser'
[6]: https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook?tabs=newteams%2Cdotnet/ 'Create Incoming Webhooks'
[7]: https://niquests.readthedocs.io/en/latest/user/quickstart.html#timeouts/ 'Niquests Quickstart' 