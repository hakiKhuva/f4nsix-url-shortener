const copyToClipboard = (data) => {
    navigator.clipboard.writeText(data)
    alert("Copied to clipboard successfully.")
}