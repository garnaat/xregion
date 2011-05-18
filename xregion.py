import boto.ec2
from boto.exception import EC2ResponseError

class ServiceMap(dict):

    def __init__(self, region_names=None):
        dict.__init__(self)
        if not region_names:
            region_names = [ r.name for r in boto.ec2.regions() ]
        self.region_names = region_names
        self.connect()

    def connect(self, **kwargs):
        for region_name in self.region_names:
            self[region_name] = boto.ec2.connect_to_region(region_name, **kwargs)
            
        
class XRegionResource(dict):

    def __init__(self, service_map, **kwargs):
        dict.__init__(self)
        self.service_map = service_map
        self.kwargs = kwargs
        for conn in self.service_map.values():
            resource = self.exists(conn)
            if not resource:
                resource = self.create(conn)
            self[conn.region.name] = resource

    def exists(self, conn):
        pass

    def create(self, conn):
        pass

class KeyPairResource(XRegionResource):

    def exists(self, conn):
        resource = None
        try:
            resource = conn.get_all_key_pairs([self.kwargs['key_name']])[0]
        except EC2ResponseError as e:
            if e.error_code != 'InvalidKeyPair.NotFound':
                raise e
        return resource

    def create(self, conn):
        print 'Creating key %s in region %s' % (self.kwargs['key_name'], conn.region.name)
        return conn.import_key_pair(**self.kwargs)
        
class SecurityGroupResource(XRegionResource):

    def exists(self, conn):
        resource = None
        try:
            resource = conn.get_all_security_groups([self.kwargs['name']])[0]
        except EC2ResponseError as e:
            if e.error_code != 'InvalidGroup.NotFound':
                raise e
        return resource

    def create(self, conn):
        print 'Creating group %s in region %s' % (self.kwargs['name'], conn.region.name)
        return conn.create_security_group(**self.kwargs)
        
class ImageResource(XRegionResource):

    def exists(self, conn):
        resource = None
        l = conn.get_all_images(filters={'name' : self.kwargs['name']})
        if len(l) > 0:
            resource = l[0]
        return resource

    def create(self, conn):
        raise ValueError("Can't create image in region %s" % conn.region.name)


image_name = 'ebs/ubuntu-images/ubuntu-maverick-10.10-amd64-server-20101225'

