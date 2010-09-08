# Copyright (c) 2010 Chris Moyer http://coredumped.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import boto
from boto.connection import AWSQueryConnection, AWSAuthConnection
import time
import urllib
import xml.sax
from boto.ecs.item import Item
from boto import handler
from boto.resultset import ResultSet

class ECSConnection(AWSQueryConnection):
    """ECommerse Connection"""

    APIVersion = '2010-09-01'
    SignatureVersion = '2'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, host='ecs.amazonaws.com',
                 debug=0, https_connection_factory=None, path='/'):
        AWSQueryConnection.__init__(self, aws_access_key_id, aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port, proxy_user, proxy_pass,
                                    host, debug, https_connection_factory, path)

    def make_request(self, action, params=None, path='/', verb='GET'):
        """Overriden because we don't do the "Action" setting here"""
        headers = {}
        if params == None:
            params = {}
        params['Version'] = self.APIVersion
        params['AWSAccessKeyId'] = self.aws_access_key_id
        params['SignatureVersion'] = self.SignatureVersion
        params['Timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        qs, signature = self.get_signature(params, verb, self.get_path(path))
        if verb == 'POST':
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            request_body = qs + '&Signature=' + urllib.quote(signature)
            qs = path
        else:
            request_body = ''
            qs = path + '?' + qs + '&Signature=' + urllib.quote(signature)
        return AWSAuthConnection.make_request(self, verb, qs,
                                              data=request_body,
                                              headers=headers)


    def get_response(self, action, params, list_marker):
        """
        Utility method to handle calls to ECS and parsing of responses.
        """
        params['Service'] = "AWSECommerceService"
        params['Operation'] = action
        response = self.make_request("GET", params, "/onca/xml")
        body = response.read()
        boto.log.debug(body)

        if response.status != 200:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)

        rs = ResultSet([('Item', Item)])
        h = handler.XmlHandler(rs, self)
        xml.sax.parseString(body, h)
        return rs

    #
    # Group methods
    #
    
    def item_search(self, search_index, **params):
        """
        Returns items that satisfy the search criteria, including one or more search 
        indices.

        For a full list of search terms, 
        :see: http://docs.amazonwebservices.com/AWSECommerceService/2010-09-01/DG/index.html?ItemSearch.html
        """
        params['SearchIndex'] = search_index
        return self.get_response('ItemSearch', params, list_marker="Items")
