from flask import Flask, render_template, request, jsonify
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info
import datetime

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', host_ips=host_ips)


host_ips = {
    'h1': '10.0.0.1',
    'h2': '10.0.0.2',
    'h3': '11.0.0.1',
    'h4': '192.168.1.1',
    'h5': '10.8.1.1'
}

net = None



# ----
# ITA
# La funzione "create_network" configura e crea la rete Mininet, aggiungendo controller, switch, host, router e link.
# Imposta i parametri di rete come le velocità di banda e i ritardi dei collegamenti.
# Avvia anche la rete e configura il forwarding dei pacchetti sui router.
# ----- 
# ENG
# The "create_network" function configures and creates the Mininet network, adding controllers, switches, hosts, routers, and links.
# It sets network parameters such as link bandwidth and delay.
# It also starts the network and configures packet forwarding on the routers.
# -----
def create_network():
    global net
    setLogLevel('info')
    net = Mininet(controller=RemoteController, link=TCLink, switch=OVSKernelSwitch)

    info('--- Adding controller ---\n')
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    info('--- Adding switches ---\n')
    sw1 = net.addSwitch('sw1')
    sw3 = net.addSwitch('sw3')
    sw4 = net.addSwitch('sw4')
    sw5 = net.addSwitch('sw5')

    info('--- Adding hosts ---\n')
    h1 = net.addHost('h1', ip='10.0.0.1/24', defaultRoute='via 10.0.0.254')
    h2 = net.addHost('h2', ip='10.0.0.2/24', defaultRoute='via 10.0.0.254')
    h3 = net.addHost('h3', ip='11.0.0.1/24', defaultRoute='via 11.0.0.254')
    h4 = net.addHost('h4', ip='192.168.1.1/24', defaultRoute='via 192.168.1.254')
    h5 = net.addHost('h5', ip='10.8.1.1/24', defaultRoute='via 10.8.1.254')

    info('--- Adding routers ---\n')
    r1 = net.addHost('r1', ip='10.0.0.254/24')
    r2 = net.addHost('r2', ip='11.0.0.254/24')
    r3 = net.addHost('r3', ip='192.168.1.254/24')
    r4 = net.addHost('r4', ip='10.8.1.254/24')

    info('--- Creating links ---\n')
    net.addLink(h1, sw1, bw=100, delay='0.05ms')
    net.addLink(h2, sw1, bw=100, delay='0.05ms')
    net.addLink(h3, sw5, bw=1, delay='0.5ms')
    net.addLink(h4, sw3, bw=100, delay='0.05ms')
    net.addLink(h5, sw4, bw=100, delay='0.05ms')

    net.addLink(sw1, r1, bw=100, delay='0.05ms')
    net.addLink(sw5, r2, bw=20, delay='2ms')
    net.addLink(sw3, r3, bw=1, delay='2ms')
    net.addLink(sw4, r4, bw=1, delay='2ms')

    net.addLink(r1, r2, intfName1='r1-eth1', params1={'ip': '200.0.0.1/30'},
                intfName2='r2-eth1', params2={'ip': '200.0.0.2/30'}, bw=1, delay='2ms')
    net.addLink(r1, r3, intfName1='r1-eth2', params1={'ip': '170.0.0.1/30'},
            intfName2='r3-eth1', params2={'ip': '170.0.0.2/30'}, bw=5, delay='2ms')
    net.addLink(r2, r4, intfName1='r2-eth2', params1={'ip': '180.1.2.1/30'},
                intfName2='r4-eth1', params2={'ip': '180.1.2.2/30'}, bw=20, delay='2ms')

    info('--- Starting network ---\n')
    net.start()

    info('--- Configuring routers ---\n')
    for router in [r1, r2, r3, r4]:
        router.cmd('sysctl -w net.ipv4.ip_forward=1')

    info('--- Setting up static routes ---\n')
    r1.cmd('ip route add 11.0.0.0/24 via 200.0.0.2 dev r1-eth1')
    r1.cmd('ip route add 192.168.1.0/24 via 170.0.0.2 dev r1-eth2')
    r1.cmd('ip route add 10.8.1.0/24 via 200.0.0.2 dev r1-eth1')

    r2.cmd('ip route add 10.0.0.0/24 via 200.0.0.1 dev r2-eth1')
    r2.cmd('ip route add 192.168.1.0/24 via 180.1.2.2 dev r2-eth2')
    r2.cmd('ip route add 10.8.1.0/24 via 180.1.2.2 dev r2-eth2')

    r3.cmd('ip route add 10.0.0.0/24 via 170.0.0.1 dev r3-eth1')
    r3.cmd('ip route add 11.0.0.0/24 via 170.0.0.1 dev r3-eth1')
    r3.cmd('ip route add 10.8.1.0/24 via 170.0.0.1 dev r3-eth1')

    r4.cmd('ip route add 10.0.0.0/24 via 180.1.2.1 dev r4-eth1')
    r4.cmd('ip route add 11.0.0.0/24 via 180.1.2.1 dev r4-eth1')
    r4.cmd('ip route add 192.168.1.0/24 via 180.1.2.1 dev r4-eth1')



    info('--- Network created successfully ---\n')


# ----
# ITA
# La funzione "parse_iperf_output" elabora l'output di iperf, suddividendolo in righe e formattandolo a seconda del protocollo (TCP o UDP).
# Aggiunge informazioni come il timestamp, l'indirizzo IP e la velocità di trasferimento e rende il tutto più 'human-readable'
# ----- 
# ENG
# The function `parse_iperf_output` processes the iperf output, splitting it into lines and formatting it based on the protocol (TCP or UDP).
# It adds details such as the timestamp, IP address, and transfer speed, and makes everything more 'human-readable'
# -----
def parse_iperf_output(output, protocol):
    lines = output.strip().split('\n')
    parsed_lines = []
    
    for line in lines:
        fields = line.split(',')
        parsed_line = {}

        if protocol == 'TCP' and len(fields) >= 8:
            parsed_line = {
                "timestamp": format_timestamp(fields[0]),
                "src_ip": fields[1],
                "src_port": fields[2],
                "dest_ip": fields[3],
                "dest_port": fields[4],
                "id": fields[5],
                "interval": format_interval(fields[6]),
                "transfer": format_transfer(fields[7]),
                "bandwidth": format_bandwidth(fields[8]) if len(fields) > 8 else "N/A",
            }
        elif protocol == 'UDP' and len(fields) >= 12:
            try:
                total_packets = int(fields[7])  
                lost_packets = int(fields[10])
                packet_loss_percentage = (lost_packets / total_packets) * 100 if total_packets > 0 else 0
            except (ValueError, ZeroDivisionError):
                packet_loss_percentage = "N/A"

          
            parsed_line = {
                "timestamp": format_timestamp(fields[0]),
                "src_ip": fields[1],
                "src_port": fields[2],
                "dest_ip": fields[3],
                "dest_port": fields[4],
                "id": fields[5],
                "interval": format_interval(fields[6]),
                "transfer": format_transfer(fields[7]),
                "bandwidth": format_bandwidth(fields[8]),
                "jitter_ms": f"{fields[9]} ms",
                "packet_loss": fields[10],
                "packet_loss_percentage": f"{packet_loss_percentage:.2f}%"
            }
        else:
            parsed_line = {} 
        
        parsed_lines.append(parsed_line)

    return parsed_lines



def format_timestamp(timestamp):
    try:
        dt = datetime.datetime.strptime(timestamp, '%Y%m%d%H%M%S')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return timestamp  

def format_interval(interval):
    try:
        start, end = map(float, interval.split('-'))
        return f"{start:.1f}s-{end:.1f}s"
    except ValueError:
        return interval 

def format_transfer(transfer):
    try:
        bytes_transferred = int(transfer)
        kb_transferred = bytes_transferred / 1024  # Converti in KB
        return f"{bytes_transferred} ({kb_transferred:.0f} KB)"
    except ValueError:
        return transfer 

def format_bandwidth(bandwidth):
    try:
        bps = int(bandwidth)
        kbps = bps / 1000  
        return f"{bps} ({kbps:.0f} Kbps)"
    except ValueError:
        return bandwidth 



# ----
# ITA
# La funzione "start_iperf_test" esegue il test iperf per misurare la velocità della rete tra due host specifici.
# Avvia il server iperf su uno degli host e il client iperf sull'altro, quindi restituisce i risultati analizzati.
# ----- 
# ENG
# The "start_iperf_test" function runs the iperf test to measure the network speed between two specified hosts.
# It starts the iperf server on one host and the iperf client on the other, then returns the analyzed results.
# -----
@app.route('/start_iperf', methods=['POST'])
def start_iperf():
    data = request.json
    selected_ip = data.get('ip_dest')
    selected_rate = data.get('src_rate')
    selected_protocol = data.get('l4_proto')

    if not selected_ip or not selected_rate or not selected_protocol:
        return jsonify({'status': 'error', 'message': 'All parameters must be selected.'}), 400

    try:
        host = net.get('h1')
        if not host:
            return jsonify({'status': 'error', 'message': 'Unable to find h1'}), 500

        if selected_protocol == 'TCP':
            cmd = f'iperf -c {selected_ip} -b {selected_rate} -t 10 -y C'
        elif selected_protocol == 'UDP':
            cmd = f'iperf -c {selected_ip} -u -b {selected_rate} -t 10 -y C'
        else:
            return jsonify({'status': 'error', 'message': 'Invalid protocol.'}), 400

        output = host.cmd(cmd)
        
        if "connect failed" in output or "Connection refused" in output:
            return jsonify({'status': 'error', 'message': f'Iperf failed: {output}'})

        parsed_output = parse_iperf_output(output, selected_protocol)

        return jsonify({
            'status': 'success',
            'message': f'Iperf started to {selected_ip} with rate {selected_rate} and protocol {selected_protocol}.',
            'output': parsed_output 
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500




# ----
# ITA
# La funzione "stop" interrompe la rete Mininet, fermando tutti i processi in esecuzione, inclusi gli host, i router e i controller.
# Viene chiamato il metodo "stop()" su "net" per arrestare l'intera rete.
# Dopo l'arresto della rete, la variabile "net" viene impostata su None e non si può rieseguire un nuovo test
# ----- 
# ENG
# The "stop" function halts the Mininet network, stopping all running processes including hosts, routers, and controllers.
# The "stop()" method is called on "net" to shut down the entire network.
# After stopping the network, the "net" variable is set to None and a new test cannot be re-run
# -----
@app.route('/stop_iperf', methods=['POST'])
def stop_iperf():
    try:
        host = net.get('h1')
        if not host:
            return jsonify({'status': 'error', 'message': 'Unable to find h1'}), 500

        host.cmd('pkill -f iperf')
        return jsonify({'status': 'success', 'message': 'Iperf stopped successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500




# ----
# ITA
# La funzione "restart" arresta la rete corrente (se presente) e la ricrea da capo chiamando "create_network".
# In pratica, la funzione esegue un arresto e riavvio della rete Mininet.
# Questo può essere utile per applicare modifiche alla rete o ripristinare una configurazione di rete pulita.
# Dopo aver chiamato "create_network", la rete viene riavviata correttamente.
# ----- 
# ENG
# The "restart" function stops the current network (if any) and recreates it from scratch by calling "create_network".
# Essentially, the function make a stop and restart cycle for the Mininet network.
# This can be useful for applying network changes or resetting the network to a clean configuration.
# After calling "create_network", the network is properly restarted.
# -----
@app.route('/restart_iperf', methods=['POST'])
def restart_iperf():
    protocol = request.args.get('protocol')

    if not protocol or protocol not in ["TCP", "UDP"]:
        return jsonify({"error": "Invalid or missing protocol"}), 400

    try:
      
        for host in net.hosts:
            if host.name.startswith('h'):
                host.cmd('pkill -f iperf')
        
       
        for host in net.hosts:
            if host.name.startswith('h'):
                if protocol == "TCP":
                    host.popen(f'iperf -s -y C >> {host.name}_log.csv', shell=True)
                else:  
                    host.popen(f'iperf -s -u -y C >> {host.name}_log.csv', shell=True)

        return jsonify({"status": f"iperf restarted in {protocol} mode for all hosts"}), 200
    except Exception as e:
        return jsonify({"error": f"Error restarting iperf: {str(e)}"}), 500

if __name__ == '__main__':
    create_network()
    app.run(host='0.0.0.0', port=5000)

