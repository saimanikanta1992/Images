import csv
from burp import IBurpExtender, IContextMenuFactory, IContextMenuInvocation, ITab
from javax.swing import JPanel, JLabel, JTextField, JButton, JMenuItem, SwingUtilities
import threading

class BurpExtender(IBurpExtender, IContextMenuFactory, ITab):
    def __init__(self):
        self.selected_request = None
        self.selected_description = ""
        self.request_data = []  # List to store (request, description) tuples
        self.panel = JPanel()  # Initialize the panel
        self.description_field = None
        self.export_button = None  # Initialize the export button here

    def registerExtenderCallbacks(self, callbacks):
        # Set the name of the extension
        callbacks.setExtensionName("Hello World Repeater Subtab with Context Menu and Export")

        # Store the callbacks and helpers
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()

        # Register the custom tab in the Burp Suite UI
        callbacks.addSuiteTab(self)

        # Register the custom context menu in the Repeater
        callbacks.registerContextMenuFactory(self)

    def getTabCaption(self):
        # The "caption" of the subtab under the Repeater tab
        return "Hello World Subtab"

    def getUiComponent(self):
        # Check if the request is valid before updating the UI
        if self.selected_request:
            # If a request is marked as valid, display it
            request_str = self._helpers.bytesToString(self.selected_request)
            label = JLabel("Valid Request: %s..." % request_str[:50])  # Display part of the request string

            # Initialize the description field and save button only when needed
            if not self.description_field:
                self.description_field = JTextField(self.selected_description, 30)

            if not self.export_button:
                self.export_button = JButton("Export Report", actionPerformed=self.export_report)

            save_button = JButton("Save Description", actionPerformed=self.save_description)

            # Update panel contents in the event dispatch thread (EDT)
            SwingUtilities.invokeLater(lambda: self.update_panel(label, save_button))
        else:
            # Otherwise, show a default message
            label = JLabel("Hello, World! No request marked as valid.")
            # Update panel contents in the event dispatch thread (EDT)
            SwingUtilities.invokeLater(lambda: self.update_panel(label))

        return self.panel

    def update_panel(self, label, save_button=None):
        # This method is invoked in the EDT to update the UI components.
        self.panel.removeAll()  # Clear previous content
        self.panel.add(label)

        if save_button:
            self.panel.add(self.description_field)
            self.panel.add(save_button)

        if self.export_button:
            self.panel.add(self.export_button)  # Add the export button to the panel

        self.panel.revalidate()
        self.panel.repaint()

    def createMenuItems(self, invocation):
        # Create the context menu item for marking a request as valid
        menu_item = JMenuItem("Mark as Valid")
        menu_item.addActionListener(lambda x: self.mark_as_valid(invocation))
        return [menu_item]

    def mark_as_valid(self, invocation):
        # This method marks the selected HTTP request as valid
        selected_message = invocation.getSelectedMessages()[0]
        self.selected_request = selected_message.getRequest()  # Get the HTTP request bytes
        self.selected_description = ""  # Reset description for the new request
        self._callbacks.issueAlert("Request marked as valid. Add a description and save it.")

        # Refresh the HelloWorld subtab to display the marked request
        threading.Thread(target=self.refresh_tab).start()

    def save_description(self, event):
        # Save the description for the current request
        description = self.description_field.getText()
        if self.selected_request:
            self.selected_description = description
            # Add the request and description to the request_data list
            self.request_data.append((self.selected_request, self.selected_description))
            self._callbacks.issueAlert("Description saved for the request.")
        else:
            self._callbacks.issueAlert("No valid request selected!")

    def refresh_tab(self):
        # This method forces the Burp Suite UI to refresh the HelloWorld subtab
        self._callbacks.removeSuiteTab(self)  # Temporarily remove the tab
        self._callbacks.addSuiteTab(self)  # Re-add the tab to trigger UI update

    def export_to_csv(self, filepath):
        # Export the saved request data and descriptions to a CSV file
        try:
            # Open the file in text mode with proper encoding for both Python 2 and Python 3
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Request', 'Description'])  # Write header row
                for request, description in self.request_data:
                    # Convert request bytes to string for CSV
                    request_str = self._helpers.bytesToString(request)
                    writer.writerow([request_str, description])

            # Issue a proper alert with a message
            self._callbacks.issueAlert("Data successfully exported to %s" % filepath)
        except Exception as e:
            # Proper exception handling and alert display
            self._callbacks.issueAlert("Error exporting data")

    def export_report(self, event):
        # Specify the file path for your CSV file
        file_path = "/path/to/your/report.csv"  # Update with desired path
        self.export_to_csv(file_path)
