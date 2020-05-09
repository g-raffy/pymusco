SCANS = samples/scans/007-captain-future-galaxy-drift-1.pdf

samples: $(SCANS)

# make sure that imagemagick's convert program is allowed to read and write pdfs (see https://cromwell-intl.com/open-source/pdf-not-authorized.html) :
# in /etc/ImageMagick-6/policy.xml, replace
#   <policy domain="coder" rights="none" pattern="PDF" />
# with
#   <policy domain="coder" rights="read|write" pattern="PDF" />

samples/scans/007-captain-future-galaxy-drift-1.pdf: samples/origpdf/007-captain-future-galaxy-drift-1-parts.pdf
	./bin/scanify $< $@

.PHONY: clean
clean:
	rm -f $(SCANS)
	rm -f samples/stubs/007-captain-future-galaxy-drift-1.pdf
	rm -f samples/prints/007-captain-future-galaxy-drift-1.pdf
	rm -f samples/prints/007-captain-future-galaxy-drift-1-saxo-soprano.pdf

samples/stubs/007-captain-future-galaxy-drift-1.pdf: samples/harmony.orchestra samples/scans/007-captain-future-galaxy-drift-1.pdf samples/scans/007-captain-future-galaxy-drift-1.desc  
	PYTHONPATH=./src ./src/pymusco.py --orchestra-file-path $(word 1,$^) build-stub --scan-file-path $(word 2,$^) --scan-desc-file-path $(word 3,$^) --stub-file-path $@

samples/prints/007-captain-future-galaxy-drift-1.pdf: samples/harmony.orchestra samples/stubs/007-captain-future-galaxy-drift-1.pdf samples/orchestra.headcount 
	PYTHONPATH=./src ./src/pymusco.py --orchestra-file-path $(word 1,$^) build-print --stub-file-path $(word 2,$^) --print-file-path $@ ts-auto --headcount-file-path $(word 3,$^)

samples/prints/007-captain-future-galaxy-drift-1-saxo-soprano.pdf: samples/harmony.orchestra samples/stubs/007-captain-future-galaxy-drift-1.pdf 
	PYTHONPATH=./src ./src/pymusco.py --orchestra-file-path $(word 1,$^) build-print --stub-file-path $(word 2,$^) --print-file-path $@ ts-single 'bb soprano saxophone'


.PHONY: test
test: samples/prints/007-captain-future-galaxy-drift-1.pdf samples/prints/007-captain-future-galaxy-drift-1-saxo-soprano.pdf

