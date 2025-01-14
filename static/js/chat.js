let scroller = document.querySelector("#scroller");
let anchor = document.querySelector("#anchor");

function onLoad() {
    console.log('onLoad')
    let messageInput = document.getElementById('message')
    let submitButton = document.getElementById('send-message')
    
    const targetNode = document.getElementById('scroller');
    const config = { childList: true };
    
    const callback = function (mutationsList, observer) {
        for (let mutation of mutationsList) {
          if (mutation.type === "childList") {
            window.scrollTo(0, document.body.scrollHeight);
          }
        }
      };
    
    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);

    scroller.insertBefore(document.getElementById('messages'), anchor)

    messageInput.addEventListener('input', (event) => {
        if (event.target.value.length > 0) {
            submitButton.classList.remove('disabled')
        } else {
            submitButton.classList.add('disabled')
        }
    })

    function addMessageToChat(message) {
        let messageHTML = ''
        if (message.author === 'assistant') {
            messageHTML = `
                <div class="d-flex flex-row justify-content-start mb-4">
                    <img class="bg-gray" src="static/img/salfatix_avatar.png" alt="avatar 1" style="width: 65px; height: 100%;">
                    <div class="p-3 ms-3" style="border-radius: 15px; background-color: rgba(57, 192, 237, .2);">
                        <p class="mb-0">${message.content}</p>
                    </div>
                </div>
            `;
        } else {
            messageHTML = `
                <div class="d-flex flex-row justify-content-end mb-4">
                    <div class="p-3 me-3 border bg-body-tertiary" style="border-radius: 15px;">
                        <p class="mb-0">${message.content}</p>
                    </div>
                </div>
            `
        }

        let messages = document.getElementById('messages')
        messages.insertAdjacentHTML('beforeend', messageHTML)        
        scroller.insertBefore(messages, anchor)
    }

    document.addEventListener('submit', async (event) => {
        event.preventDefault()

        const form = event.target
        const formData = new FormData(form)

        let content_message = ""
        if (formData.get('message') == null){            
            content_message = event.submitter.defaultValue
            formData.set('message', content_message)            
        }
        else
        {
            content_message  = formData.get('message')
            submitButton.classList.add('disabled')
            messageInput.classList.add('disabled')
            submitButton.value = 'Enviando...'    
            messageInput.value = ''
        }

        addMessageToChat({
            content: content_message,
            author: 'user',
        })        

        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
               'Accept': 'application/json',
            },
            body: formData,
        })

        const message = await response.json()
        addMessageToChat(message)
        messageInput.classList.remove('disabled')        
        submitButton.value = 'Enviar'
    })
}

document.addEventListener('DOMContentLoaded', onLoad)