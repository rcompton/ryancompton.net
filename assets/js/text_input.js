const submitButton = document.getElementById("submitButton");
      const userInput = document.getElementById("userInput");

      submitButton.addEventListener("click", () => {
        const text = userInput.value;
        const requestOptions = {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
        };

        fetch("https://example.com/api", requestOptions)
          .then(response => response.json())
          .then(data => console.log(data))
          .catch(error => console.log(error));
      });
