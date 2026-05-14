import download from "downloadjs"

import { createSlugLastName } from "../exporter/tools/slugs"
import { createSlug } from "../exporter/tools/file"

import { HTMLExporter } from "../exporter/html"
import { DOCXExporter } from "../exporter/docx"
import { config } from "./config"

export class DhdConfHtmlExporter extends HTMLExporter {
    init() {
        this.styleSheets.push({url: staticUrl("css/dhdconf_export_html.css")})
        this.converterOptions.affiliationNumbering = "alpha"
        return super.init()
    }

    download(blob) {
        console.log(this.metaData.authors[0].attrs.lastname)
        const joder = createSlugLastName(this.metaData.authors[0].attrs.lastname)
        const nuestrotitulo = createSlug(this.docTitle)
        return download(blob, `${joder}-${nuestrotitulo}.html.zip`, this.mimeType)
    }

        
}

export class DhdConfDocxExporter extends DOCXExporter {
    init() {
        if (config.docxRemoveComments) {
            this.doc = structuredClone(this.doc)
            this.doc.comments = {}
        }
        return super.init()
    }
}
