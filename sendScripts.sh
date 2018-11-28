#!/usr/bin/env bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/geni_cert_portal_key
scp ./s_tcp_node.py s:~/
scp ./b_tcp_udp_node.py B:~/
scp ./r1_udp_node.py r1:~/
scp ./r2_udp_node.py r2:~/
scp ./d_udp_node.py d:~/