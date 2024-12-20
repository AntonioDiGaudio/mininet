// ----
// ITA
//"selectedIP" e "selectedProtocol" sono variabili che memorizzano rispettivamente l'indirizzo IP e il protocollo selezionati dall'utente. 
//Inizialmente sono impostati su null, indicando nessuna selezione.
// ----
// ENG
// "selectedIP" and "selectedProtocol" are variables that store the IP address and protocol selected by the user, respectively. 
//They are initially set to null, indicating no selection.
// ----
let selectedIP = null;
let selectedProtocol = null;


// ----
// ITA
// Questa funzione imposta il protocollo selezionato e aggiorna l'aspetto dei pulsanti per evidenziare quale protocollo è stato scelto. 
//Seleziona un protocollo e aggiunge la classe button-selected al pulsante corrispondente.
// ----- 
// ENG
//This function sets the selected protocol and updates the appearance of the buttons to highlight which protocol has been chosen. 
//Selects a protocol and adds the button-selected class to the corresponding button.
// ----- 
function setProtocol(protocol, button) {
    selectedProtocol = protocol;

    const protocolButtons = document.querySelectorAll('.protocol-button');
    protocolButtons.forEach(btn => btn.classList.remove('button-selected'));

    button.classList.add('button-selected');
}




// ----
// ITA
// Questa funzione imposta l'IP selezionato e aggiorna l'aspetto dei pulsanti per evidenziare quale IP è stato scelto. 
// Seleziona un IP e aggiunge la classe button-selected al pulsante corrispondente.
// ----- 
// ENG
// This function sets the selected IP and updates the appearance of the buttons to highlight which IP has been chosen. 
// Selects an IP and adds the button-selected class to the corresponding button.
// -----
function setIP(ip, button) {
    selectedIP = ip;

    const hostButtons = document.querySelectorAll('.host-button');
    hostButtons.forEach(btn => btn.classList.remove('button-selected'));

    button.classList.add('button-selected');
}




// ----
// ITA
// Questa funzione avvia il test iperf, controllando che tutti i parametri necessari (IP, protocollo, velocità) siano stati selezionati.
// Se tutto è corretto, invia la richiesta al server per avviare il test e gestisce la risposta, 
// mostrando i risultati nel formato appropriato.
// ----- 
// ENG
// This function starts the iperf test, checking that all the necessary parameters (IP, protocol, rate) have been selected. 
// If everything is correct, it sends a request to the server to start the test 
// and handles the response, displaying the results in the appropriate format.
// -----
function startIperf() {
    toggleLoader(true);  
    const srcRate = document.getElementById('src_rate').value;
    if (!selectedIP || !srcRate || !selectedProtocol) {
        alert("Seleziona tutti i parametri prima di avviare.");
        toggleLoader(false);  
        return;
    }

    fetch('/start_iperf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            ip_dest: selectedIP,
            src_rate: srcRate,
            l4_proto: selectedProtocol,
        }),
    })
        .then(response => response.json())
        .then(data => {
            toggleLoader(false);  
            document.getElementById('results-title').style.display = 'block';
            document.getElementById('output').style.display = 'block';
            const outputElement = document.getElementById('output');
            outputElement.innerHTML = '';  

            // Mostra i dati elaborati
            if (Array.isArray(data.output)) {
                data.output.forEach(entry => {
                    const entryDiv = document.createElement('div');
                    entryDiv.classList.add('output-entry');

                    for (const [key, value] of Object.entries(entry)) {
                        const line = document.createElement('p');
                        line.innerText = `${key}: ${value}`;
                        entryDiv.appendChild(line);
                    }

                    outputElement.appendChild(entryDiv);
                });
            } else {
                outputElement.innerText = data.output;  
            }
        })
        .catch(error => {
            toggleLoader(false);  
            console.error('Errore:', error);
        });
}





// ----
// ITA
// Questa funzione invia una richiesta al server per fermare il test iperf in corso. Una volta ricevuta la risposta,
// mostra il messaggio di stato o errore.
// ----- 
// ENG
// This function sends a request to the server to stop the ongoing iperf test. Once the response is received, 
// it displays the status or error message.
// -----
function stopIperf() {
    toggleLoader(true);  
    fetch('/stop_iperf', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            toggleLoader(false); 
            document.getElementById('output').innerText = data.message;
        })
        .catch(error => {
            toggleLoader(false); 
            console.error('Errore:', error);
        });
}


function toggleLoader(show) {
    const loader = document.getElementById('loader');
    if (show) {
        loader.style.display = 'flex';  
    } else {
        loader.style.display = 'none'; 
    }
}




// ----
// ITA
// Questa funzione invia una richiesta per riavviare il test iperf con un protocollo specifico (TCP o UDP). 
// Gestisce la risposta dal server, mostrando uno stato o un errore in caso di problemi.
// ----- 
// ENG
// This function sends a request to restart the iperf test with a specific protocol (TCP or UDP). 
// It handles the server's response, displaying a status or error message in case of issues.
// -----
function restartIperf(protocol) {
    fetch('/restart_iperf?protocol=' + protocol, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            alert(data.status); 
        } else if (data.error) {
            alert('Error: ' + data.error);  
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while restarting iperf.');
    });
}






// ----
// ITA
// Al caricamento della pagina, questa parte del codice aggiunge dei listener per i pulsanti che selezionano i protocolli (UDP e TCP). 
// Quando un pulsante viene cliccato, viene selezionato il protocollo e il test iperf viene riavviato con il protocollo scelto.
// ----- 
// ENG
// On page load, this part of the code adds event listeners to the buttons that select the protocols (UDP and TCP). 
// When a button is clicked, the protocol is selected, and the iperf test is restarted with the chosen protocol.
// -----
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('udp-button').addEventListener('click', () => {
        setProtocol('UDP', document.getElementById('udp-button'));
        restartIperf('UDP');
    });

    document.getElementById('tcp-button').addEventListener('click', () => {
        setProtocol('TCP', document.getElementById('tcp-button'));
        restartIperf('TCP');
    });
});
