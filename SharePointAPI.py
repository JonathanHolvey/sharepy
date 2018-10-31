import re
import requests
import xml.dom.minidom as dom

class spListsAPI():
    """
    A SharePoint Online lists API. For a full listing of commands available to your
    SP site, check your https://tenant.sharepoint.com/sites/subsite/_vti_bin/lists.asmx file.
    
    This class is intended to be used on the driver code side of the SharePointSession class
    of sharepy
    An adaptation of https://github.com/thybag/PHP-SharePoint-Lists-API/
    """

    def __init__(self, SP_SESSION=None):
        self.SP_SESSION = SP_SESSION
        self.spsTenantUrl = SP_SESSION.tenantUrl
        self.spsBase = "https://"+ re.search('((^.+/sites/[^/]+/))', SP_SESSION.site).group(1) + "_vti_bin/Lists.asmx"
        self.SP_SESSION.headers.update({"Content-Type":"text/xml; charset=utf-8", "Content-Length":"length", "Host":self.SP_SESSION.tenantUrl})

    '''
    Requires no extra data in the SOAP envelope
    '''
    def GetListCollection(self):
        self.SP_SESSION.headers.update({"SOAPAction": "http://schemas.microsoft.com/sharepoint/soap/GetListCollection"})
        envelope = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">  <soap:Body>    <GetListCollection xmlns="http://schemas.microsoft.com/sharepoint/soap/" />  </soap:Body></soap:Envelope>'
        res = requests.post(url=self.spsBase, data=envelope, headers=self.SP_SESSION.headers, cookies=self.SP_SESSION.cookies)
        
        return self.getArrayFromElementsByTagName(res.text, 'List')

    '''
    Requires the following (at the least) in the SOAP envelope:
        listName
    Optional items in the envelope:
        viewName
        query
        viewFields
        rowLimit
        QueryOptions
        webID
    Note: If rowLimit is not provided, SharePoint will default to a response of 100 items
    '''
    def GetListItems(self, listName, viewName='', query='', viewFields='', rowLimit='', QueryOptions='', webID=''):
        self.SP_SESSION.headers.update({"SOAPAction": "http://schemas.microsoft.com/sharepoint/soap/GetListItems"})
        envelopeTemplate = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">  <soap:Body>    <GetListItems xmlns="http://schemas.microsoft.com/sharepoint/soap/">      <listName>{listName}</listName>      <viewName>{viewName}</viewName>      <query>{query}</query>      <viewFields>{viewFields}</viewFields>      <rowLimit>{rowLimit}</rowLimit>      <QueryOptions>{QueryOptions}</QueryOptions>      <webID>{webID}</webID>    </GetListItems>  </soap:Body></soap:Envelope>'
        envelope = envelopeTemplate.format(listName=listName, viewName=viewName, query=query, viewFields=viewFields, rowLimit=rowLimit, QueryOptions=QueryOptions, webID=webID)
        res = requests.post(url=self.spsBase, data=envelope, headers=self.SP_SESSION.headers, cookies=self.SP_SESSION.cookies)
        
        return self.getArrayFromElementsByTagName(res.text, 'z:row')
        
    #used to grab the <tag> nodes from the response
    # Returns a JSON
    def getArrayFromElementsByTagName (self, rawXML, tag, namespace=None):
        doc = dom.parseString(rawXML)
        nodes = doc.getElementsByTagName(tag)
        result = []
        #print(nodes[1].getAttribute('DocTemplateUrl'))
        for element in nodes:
            pairs = {}
            #print(node.attributes)
            for attrName, attrValue in element.attributes.items():
                pairs[attrName] = attrValue
            result.append(pairs)
            
        return result

