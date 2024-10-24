function onFormSubmit(e) {
    // Get the form data as a named values object
    var formData = e.namedValues;
  
    // Prepare the payload with the specific fields
    var payload = {
      'fname': formData['First Name'][0],   // Replace 'First Name' with your actual question title in the form
      'lname': formData['Last Name'][0],    // Replace 'Last Name' with your actual question title in the form
      'company': formData['Company'][0],    // Replace 'Company' with your actual question title in the form
      'contact': formData['Contact'][0]      // Replace 'Contact' with your actual question title in the form
    };
  
    // Set up the request options
    var options = {
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify(payload)
    };
  
    // Send the AJAX request to the Flask app
    UrlFetchApp.fetch('https://4323-50-227-148-194.ngrok-free.app', options); // Add the /submit endpoint
  }
  
  function setupTriggerFormSubmit() {
    var ss = SpreadsheetApp.getActive();
    ScriptApp.newTrigger('onFormSubmit')
      .forSpreadsheet(ss)
      .onFormSubmit()
      .create();
  }
  