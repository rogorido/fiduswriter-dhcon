/**
 * Normalize a string to create a slug depending on whether title or not
 *
 * @param {string} str - String to normalize
 * @param {boolean} isTitle - whether is title or not
 * @returns {string} Resulting slug.
 */
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
