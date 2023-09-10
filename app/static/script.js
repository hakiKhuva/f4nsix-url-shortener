const copyToClipboard = (data) => {
    navigator.clipboard.writeText(data)
    .then(() => {
        alert("Copied to clipboard successfully.")
    })
    .catch(() => {
        alert("Unable to copy the tracking id, you have to manually select and copy it!")
    })
}