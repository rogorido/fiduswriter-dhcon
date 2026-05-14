export const createSlugLastName = str => {
    if (str === "" || str == undefined) {
        str = gettext("UNKNOWN")
    }
    str = str.replace(/[^a-zA-Z0-9\s]/g, "")
    str = str.toLowerCase()
    str = str.replace(/\s/g, "-")
    return str.toUpperCase()
}
