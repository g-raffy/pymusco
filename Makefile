SCANS = samples/scans/007-captain-future-galaxy-drift-1-parts.pdf

samples: $(SCANS)

# make sure that imagemagick's convert program is allowed to read and write pdfs (see https://cromwell-intl.com/open-source/pdf-not-authorized.html) :
# in /etc/ImageMagick-6/policy.xml, replace
#   <policy domain="coder" rights="none" pattern="PDF" />
# with
#   <policy domain="coder" rights="read|write" pattern="PDF" />

samples/scans/007-captain-future-galaxy-drift-1-parts.pdf: samples/origpdf/007-captain-future-galaxy-drift-1-parts.pdf
	./bin/scanify $< $@

.PHONY: clean
clean:
	rm $(SCANS)