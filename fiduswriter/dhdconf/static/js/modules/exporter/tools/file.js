export const createSlug = str => {
    const slugify = str => {
        if (str === "") {
            str = gettext("Untitled")
        }
        str = str.replace(/[^a-zA-Z0-9\s]/g, "")
       str = str.toLowerCase()
        str = str.replace(/\s/g, "-")
        return str
    }

    const titleSlug = slugify(title)
//    const authorSlug = slugify(author)

console.log("titleSlug", titleSlug)

    let slug = `hola-${titleSlug}`

    if (slug.length > 40) {
        slug = slug.substring(0, 40)
    }

    return slug
}

export const createSlugLastName = str => {

        if (str === "") {
            str = gettext("Untitled")
        }
        str = str.replace(/[^a-zA-Z0-9\s]/g, "")
       str = str.toLowerCase()
        str = str.replace(/\s/g, "-")
        return upperCase(str)
    }
