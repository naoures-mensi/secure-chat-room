import  ldap;
try:
    ldap_client = ldap.initialize('ldap://ldap.tekup.tn');
    ldap_client.set_option(ldap.OPT_REFERRALS, 0);
    ldap_client.bind_s('cn=admin,dc=tekup,dc=tn', 'osboxes.org');
    print("connection success");
except ldap.LDAPError as ldap_error:
    print(ldap_error)
