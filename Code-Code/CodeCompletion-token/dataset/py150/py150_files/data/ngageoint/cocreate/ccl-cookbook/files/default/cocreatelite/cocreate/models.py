from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.safestring import mark_safe

import json
#import sshpubkeys
import markdown2

SANDBOX_STATUS_CHOICES = (
    ('req', 'Requested'),
    ('app', 'Approved'),
    ('dis', 'Disapproved'),
    ('pen', 'Pending'),
    ('avl', 'Available'),
    ('err', 'Error')
)

RELATED_MODEL_CHOICES = (
    ('prq', 'Playground Request'),
    ('srq', 'Sandbox Request')
)

DEPLOYMENT_ENVIRONMENTS = (
    ('isee', "ISEE"),
    ('aws', "Amazon Web Services"),
    ('awsp', "Amazon Web Services - Public Cloud"),
    ('drop', "Digital Ocean"),
    ('locl', "Local")
)

VM_STATES = (
    ('run', "Running"),
    ('reb', "Rebooting"),
    ('paus', "Paused"),
    ('rem', "Removing"),
    ('crt', "Creating")
)

class SshKey(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, blank=False, null=False, related_name="sshkeys")
    key = models.TextField()
    
    def fingerprint(self):
        try:
            pubkey = sshpubkeys.SSHKey(self.key)
            return pubkey.hash()
        #except sshpubkeys.InvalidKeyException:
        #    return "Invalid Key"
        except:
            """There are a small parcel of exceptions that can be throw to indicate invalid keys"""
            return ""
    
    def keytype(self):
        try:
            pubkey = sshpubkeys.SSHKey(self.key)
            return "%s (%d bit)" % (pubkey.key_type.decode('ascii'), pubkey.bits)
        #except sshpubkeys.InvalidKeyException:
        #    return "Invalid Key"
        except:
            """There are a small parcel of exceptions that can be throw to indicate invalid keys"""
            return ""
    
    def isValid(self):
        try:
            pubkey = sshpubkeys.SSHKey(self.key)
            return True
        except:
            return False

class UserConfigManager(models.Manager):
    
    def findOrCreate_ProxyHttp(self, user):
        """
        Find the existing Proxy or create a new blank one.
        """
        objs = super(UserConfigManager, self).get_queryset().filter(key = "proxyhttp")
        
        if len(objs) > 0:
            print ("Found Proxy")
            return objs[0]
        else:
            print ("Creating blank Proxy")
            obj = super(UserConfigManager, self).create(
                label = "Proxy Http",
                key = "proxyhttp",
                val = "",
                user = user
            )
            obj.save()
            return obj
    
    def findOrCreate_ProxyHttps(self, user):
        """
        Find the existing Proxy or create a new blank one.
        """
        objs = super(UserConfigManager, self).get_queryset().filter(key = "proxyhttps")
        
        if len(objs) > 0:
            print ("Found Proxy")
            return objs[0]
        else:
            print ("Creating blank Proxy")
            obj = super(UserConfigManager, self).create(
                label = "Proxy Https",
                key = "proxyhttps",
                val = "",
                user = user
            )
            obj.save()
            return obj
    
    
    def findOrCreate_AwsSecret(self, user):
        """
        Find the existing AWS Key or create a new blank one.
        """
        objs = super(UserConfigManager, self).get_queryset().filter(key = "awssecret")
        
        if len(objs) > 0:
            print ("Found AWS Key")
            return objs[0]
        else:
            print ("Creating blank AWS Key")
            obj = super(UserConfigManager, self).create(
                label = "AWS Secret",
                key = "awssecret",
                val = "",
                user = user
            )
            obj.save()
            return obj
        
    def findOrCreate_AwsKey(self, user):
        """
        Find the existing AWS Key or create a new blank one.
        """
        objs = super(UserConfigManager, self).get_queryset().filter(key = "awskey")
        
        if len(objs) > 0:
            print ("Found AWS Key")
            return objs[0]
        else:
            print ("Creating blank AWS Key")
            obj = super(UserConfigManager, self).create(
                label = "AWS Key",
                key = "awskey",
                val = "",
                user = user
            )
            obj.save()
            return obj
    
    def hasAwsKey(self):
        objs = super(UserConfigManager, self).get_queryset().filter(key = "awskey").exclude(val = "")
        if len(objs) == 0:
            return False
        else:
            return True
        
class UserConfig(models.Model):
    label = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    val = models.TextField(blank = True, null = True)
    user = models.ForeignKey(User, blank = False, null = False, related_name="configs")
    
    objects = UserConfigManager()
    
class TestNotification(models.Model):
    text = models.CharField(max_length = 255)
    
class Repository(models.Model):
    name = models.CharField(max_length = 255)
    uri = models.CharField(max_length = 1024)
    creator = models.ForeignKey(User, blank = False, null = False, related_name="repositories")
    created_at = models.DateTimeField(auto_now_add = True)
    
class VMSandboxTag(models.Model):
    tag = models.CharField(max_length = 255)
    

class VMPlayground(models.Model):
    name = models.CharField(max_length = 255)
    creator = models.ForeignKey(User, blank = False, null = False)
    created_at = models.DateTimeField(auto_now_add = True)
    description = models.TextField(blank = True, null = True)
    description_is_markdown = models.BooleanField(null = False, default = False)
    environment = models.CharField(max_length = 4, choices = DEPLOYMENT_ENVIRONMENTS, blank = False, null = False, default = "isee")
    access_groups = models.ManyToManyField(Group, related_name="playgrounds")
    access_users = models.ManyToManyField(User, related_name="playgrounds")
    
    def desc_html(self):
        if self.description_is_markdown:
            fmt = markdown2.markdown(self.description, extras=["footnotes", "fenced-code-blocks"])
            return mark_safe(fmt)
        else:
            return self.description
    
    def getDemos(self):
        """
        Find all sandboxes that are demos
        """
        return [sandbox for sandbox in self.sandboxes.all() if sandbox.is_demo]

class VMSandbox(models.Model):
    name = models.CharField(max_length = 255)
    logical_name = models.CharField(max_length = 255, blank = False, null = False)
    creator = models.ForeignKey(User, blank = False, null = False)
    created_at = models.DateTimeField(auto_now_add = True)
    playground = models.ForeignKey(VMPlayground, related_name = "sandboxes")
    metadata = models.TextField(blank = True, null = True)
    keys = models.ManyToManyField(SshKey, related_name = "sandboxes")
    state = models.CharField(max_length = 4, choices = VM_STATES, blank=False, null=False, default="run")
    tags = models.ManyToManyField(VMSandboxTag, related_name = "sandboxes")
    is_demo = models.BooleanField(blank = False, null = False, default = False)
    repository = models.ForeignKey(Repository, blank=True, null=True, related_name="sandboxes")
    
    def recipe(self):
        """
        Try and extract a recipe from metadata
        """
        return self._getJsonMeta('recipe')
    
    def sshKeyName(self):
        return self._getJsonMeta('sshkeyname')
        
    def privateIp(self):
        return self._getJsonMeta('ip')['PrivateIpAddress']
    
    def privateDns(self):
        return self._getJsonMeta('dns')['PrivateDnsName']
        
    def awsInstanceId(self):
        return self._getJsonMeta('awsid')
        
    def ami(self):
        return self._getJsonMeta('ami')
    
    def vpc(self):
        return self._getJsonMeta('vpc')
    
    def instanceType(self):
        return self._getJsonMeta('type')
        
    def subnet(self):
        return self._getJsonMeta('subnet')
        
    def _getJsonMeta(self, key):
        try:
            meta = json.loads(self.metadata)
            return meta[key]
        except:
            return None
    
    def isInAWS(self):
        return self.playground.environment in ['aws', 'awsp']
            
    def isPausable(self):
        return self.state == 'run'
    
    def isRebootable(self):
        return self.state == 'run'
    
    def isStartable(self):
        return self.state == 'paus'
            
    def pause(self):
        self.state = "paus"
        self.save()
    
    def reboot(self):
        self.state = "reb"
        self.save()
    
    def start(self):
        self.state = "run"
        self.save()
            
class Playground(models.Model):
    name=models.CharField(max_length=100)
    owner=models.ForeignKey(User, blank=False, null=False)
    description=models.TextField(blank=True, null=True, default="")
    environment=models.CharField(max_length=4, choices=DEPLOYMENT_ENVIRONMENTS, blank=False, null=False, default="isee")

class PlaygroundRequest(models.Model):
    requested_by=models.ForeignKey(User, related_name="playground_requested_by", blank=False, null=False)
    created_at=models.DateTimeField(auto_now_add=True)
    modified_at=models.DateTimeField(auto_now=True, blank=True, null=True)
    name = models.CharField(max_length=50)
    justification = models.TextField()
    request_status=models.CharField(max_length=3, choices=SANDBOX_STATUS_CHOICES, blank=False, null=False, default="req")
    playground=models.ForeignKey(Playground, blank=False, null=False)

class SandboxTemplate(models.Model):
    """
    Each sandbox is instantiated with a template. These templates describe the basic
    features of the template.
    """
    name=models.CharField(max_length=100, null=False, blank=False)
    recipe=models.CharField(max_length=100, null=False, blank=False)
    version=models.CharField(max_length=50, null=False, blank=True)
    description=models.TextField(null=False, blank=True, default="")
    notes=models.TextField(null=False, blank=True, default="")

class Sandbox(models.Model):
    name=models.CharField(max_length=100)
    owner=models.ForeignKey(User, blank=False, null=False)
    playground=models.ForeignKey(Playground, blank=False, null=False, related_name="sandboxes")
    hostname=models.CharField(max_length=50, blank=False, null=True)
    ip_address=models.CharField(max_length=15, blank=False, null=True)
    url=models.CharField(max_length=200)

class SandboxRequest(models.Model):
    requested_by=models.ForeignKey(User, related_name="sandbox_requested_by", blank=False, null=False)
    created_at=models.DateTimeField(auto_now_add=True)
    modified_at=models.DateTimeField(auto_now=True, blank=True, null=True)
    sandbox_name = models.CharField(max_length=100)
    justification = models.TextField(null=False, blank=True)
    sandbox_lifetime = models.DateField(null=False, blank=False, default='2016-1-1')
    request_status=models.CharField(max_length=3, choices=SANDBOX_STATUS_CHOICES, blank=False, null=False, default="req")
    sandbox=models.ForeignKey(Sandbox, blank=False,null=False)
    template=models.ForeignKey(SandboxTemplate, blank=False, null=True)
    request_progress=models.FloatField(default=0)
    request_progress_msg=models.CharField(max_length=100, default='Not Started')
    
    def isAWS(self):
        return len(self.aws_options.all()) > 0

class SandboxAWSOptions(models.Model):
    """
    AWS options for a Sandbox in an Amazon Web Services backed playground.
    """
    name=models.CharField(max_length=100, null=False, blank=False)
    recipe=models.CharField(max_length=100, null=False, blank=False)
    ami=models.CharField(max_length=100, null=False, blank=False)
    vpc=models.CharField(max_length=100, null=False, blank=False)
    json=models.TextField(null=False, blank=False, default="")
    #request=models.ForeignKey(SandboxRequest, blank=False, null=False, related_name="aws_options")
        
class NotificationManager(models.Manager):
    """
    Table level functions for working with notifications.
    """
    
    def unreadForUser(self, user_id):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT n.id, n.added_at, n.owner_id, n.read, n.msg, n.related_model_type, n.related_model_id, n.progress, n.object_name, n.error FROM cocreate_notification n WHERE n.owner_id = ? and n.read = 0", (user_id,))
        result_list = []
        
        for row in cursor.fetchall():
            p = self.model(
                id = row[0],
                added_at = row[1],
                owner_id = row[2],
                read = row[3],
                msg = row[4],
                related_model_type = row[5],
                related_model_id = row[6],
                progress = row[7],
                object_name = row[8],
                error = row[9]
            )
            result_list.append(p)
        return result_list
    
    def unreadCountForUser(self, user_id):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT count(*) FROM cocreate_notification n WHERE n.owner_id = ? and n.read = 0", (user_id,))
        return cursor.fetchone()[0]
        
    def markAllReadForUser(self, user_id):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("UPDATE cocreate_notification SET read = 1 WHERE owner_id = ? and read = 0", (user_id,))
        connection.commit()
        
class Notification(models.Model):
    """
    A bit of an explanation: The Notification object can pertain to different instances of
    other models; for instance a SandboxRequest or a PlaygroundRequest. This is a one to 
    one mapping, but because a Notification isn't tied by a foreign key to a single model, 
    we need to wedge this flexibility in ourselves. Hence, the two fields:
    
        * related_model_type - Which of the other models/tables does this notification reference
        * related_model_id - What is the id of the related model.
    
    We have some convenience methods in the model to hide most of this, but some of the
    chaining of fields we're used to won't work.
    
    Otherwise, individual items can be marked as read with model methods.
    """
    added_at=models.DateTimeField(auto_now_add=True)
    owner=models.ForeignKey(User, blank=False, null=False)
    read=models.BooleanField(null=False, default=False)
    msg=models.TextField(null=False, blank=True)
    related_model_type=models.CharField(max_length=3, choices=RELATED_MODEL_CHOICES, blank=False, null=False)
    related_model_id=models.IntegerField()
    objects = NotificationManager()
    progress=models.FloatField(default=0)
    object_name=models.CharField(max_length=50, default='')
    error=models.BooleanField(null=False, default=False)
        
    def isSandboxRequest(self):
        """
        Check if this is related to a sandbox request
        """
        return self.related_model_type == 'srq'

