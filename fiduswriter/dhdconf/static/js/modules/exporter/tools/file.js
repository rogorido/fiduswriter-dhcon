// TODO: write doc to this function.
const slugify = (str, isTitle) => {
    if (str === "" && isTitle) {
        str = gettext("Untitled")
    } else if (str === "" && !isTitle) {
        str = gettext("UNKNOWN")
    }

    str = str.replace(/[^a-zA-Z0-9\s]/g, "")
    str = str.toLowerCase()
    str = str.replace(/\s/g, "-")

    return str
}

export const createSlug = str => {
    console.log("el tñiutlo es:", str)
    str = slugify(str, true)
    console.log("el tñiutlo trasnforamdo es:", str)

    if (str.length > 128) {
        str = str.substring(0, 128)
    }

    return str
}

export const createSlugLastName = str => {
    str = slugify(str, false)

    return upperCase(str)
}
