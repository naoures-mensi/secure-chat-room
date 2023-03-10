import ldap
import hashlib
import sys
from base64 import b64encode


class LdapService:
    ldap_server = "ldap://ldap.tekup.tn"  # host address
    ldap_ou = "Groups"  # organization unit
    ldap_group = "developers"  # organization sub-group
    # admin domain
    LDAP_ADMIN_DN = "cn=admin,dc=tekup,dc=tn"
    LDAP_ADMIN_PWD = "osboxes.org"

    def __init__(self, admin_pwd):
        self.password = None
        self.username = None
        self.LDAP_ADMIN_PWD = admin_pwd

    def login(self, username, password):
        self.username = username
        self.password = password
        # the following is the user_dn format provided by the ldap server
        # organization user's domain
        user_dn = "cn=" + self.username + ",cn=" + self.ldap_group + ",ou=" + \
                  self.ldap_ou + ",dc=tekup,dc=tn"
        # base domain
        ldap_base_dn = "cn=" + self.ldap_group + \
                       ",ou=" + self.ldap_ou + ",dc=tekup,dc=tn"
        # start connection
        ldap_client = ldap.initialize(self.ldap_server)
        # search for specific user
        search_filter = "cn=" + self.username
        try:
            # if authentication successful, get the full user data
            ldap_client.bind_s(user_dn, self.password)
            result = ldap_client.search_s(
                ldap_base_dn, ldap.SCOPE_SUBTREE, search_filter)
            # return all user data results
            ldap_client.unbind_s()
            return None
        except ldap.INVALID_CREDENTIALS:
            ldap_client.unbind()
            return "Wrong username or password.."
        except ldap.SERVER_DOWN:
            return "Server is down at the moment, please try again later!"
        except ldap.LDAPError as ldap_error:
            ldap_client.unbind_s()
            return "Authentication error!"

    def register(self, user):
        # base domain
        ldap_base_dn = "cn=" + self.ldap_group + ",ou=" + self.ldap_ou + ",dc=tekup,dc=tn"
        # home base
        home_base = "/home/users"
        # new user domain
        dn = 'cn=' + user['username'] + ',' + ldap_base_dn
        home_dir = home_base + '/' + user['username']
        gid = user['group_id']
        # encoding password using md5 hash function
        hashed_pwd = hashlib.md5(user['password'].encode("UTF-8"))
        # printing the equivalent byte value.
        # print("The byte equivalent of hash is : ", end="")
        # print(result.hexdigest())
        entry = []
        entry.extend([
            ('objectClass', [b'inetOrgPerson',
                             b'posixAccount', b'top']),
            ('uid', user['username'].encode("UTF-8")),
            ('givenname', user['username'].encode("UTF-8")),
            ('sn', user['username'].encode("UTF-8")),
            ('mail', user['email'].encode("UTF-8")),
            ('uidNumber', user['uid'].encode("UTF-8")),
            ('gidNumber', str(gid).encode("UTF-8")),
            ('loginShell', [b'/bin/sh']),
            ('homeDirectory', home_dir.encode("UTF-8")),
            ('userPassword', [b'{md5}' +
                              b64encode(hashed_pwd.digest())])

        ])
        # connect to host with admin
        ldap_conn = ldap.initialize(self.ldap_server)
        ldap_conn.bind_s(self.LDAP_ADMIN_DN, self.LDAP_ADMIN_PWD)
        try:
            # add entry in the directory
            ldap_conn.add_s(dn, entry)
            print("success")
            return None
        except ldap.LDAPError as ldap_error:
            print(ldap_error);
            return sys.exc_info()[0]
        finally:
            # disconnect and free memory
            ldap_conn.unbind_s()


# TESTING CONNECTION, also IGNORE the ERRORS since there's NO ERROR,
# dunno why they are being thrown,
# the attributes DO EXIST in ldap module and I VERIFIED it!
# CONNECTION WILL ONLY WORK WHEN MY SERVER IS UP

# # test case
# TODO change admin password
s = LdapService(admin_pwd="<ur_admin_pwd>")

# test login
# s.login(username="hamma", password="0000")

# test registration
user_obj = {
    'username': 'guest',
    'password': '0000',
    'email': 'u@gmail.com',
    'gender': 'male',
    'group_id': 500,  # default gid
    'uid': '1600222'  # student card
}
# s.register(user_obj)
