(vl-load-com)
(defun c:ExportCadData ( / f fn item ss i ent elist bname effname pt rot lay scx scy scz attent attdata vla-obj)
  (setq fn "G:/My Drive/1.Work/ATGT/Tool ATGT/cad_extracted_data.tsv")
  (setq f (open fn "w"))
  
  (write-line "[LAYERS]" f)
  (setq item (tblnext "layer" t))
  (while item
    (write-line (cdr (assoc 2 item)) f)
    (setq item (tblnext "layer"))
  )
  
  (write-line "[BLOCK_INSERTS]" f)
  (write-line "Name\tEffectiveName\tLayer\tX\tY\tZ\tRotation\tScaleX\tScaleY\tScaleZ\tAttributes" f)
  (setq ss (ssget "X" '((0 . "INSERT"))))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (if ent
          (progn
            (setq elist (entget ent))
            (setq bname (cdr (assoc 2 elist)))
            (setq lay (cdr (assoc 8 elist)))
            (setq pt (cdr (assoc 10 elist)))
            (setq rot (cdr (assoc 50 elist)))
            (setq scx (cdr (assoc 41 elist)))
            (setq scy (cdr (assoc 42 elist)))
            (setq scz (cdr (assoc 43 elist)))
            (if (not scx) (setq scx 1.0))
            (if (not scy) (setq scy 1.0))
            (if (not scz) (setq scz 1.0))
            (if (not rot) (setq rot 0.0))
            
            (setq effname bname)
            (setq vla-obj (vl-catch-all-apply 'vlax-ename->vla-object (list ent)))
            (if (not (vl-catch-all-error-p vla-obj))
              (if (vlax-property-available-p vla-obj 'EffectiveName)
                (setq effname (vla-get-EffectiveName vla-obj))
              )
            )
            
            (setq attstr "")
            (if (= 1 (cdr (assoc 66 elist)))
              (progn
                (setq attent (entnext ent))
                (while (and attent (/= (cdr (assoc 0 (entget attent))) "SEQEND"))
                  (setq attdata (entget attent))
                  (if (= (cdr (assoc 0 attdata)) "ATTRIB")
                    (setq attstr (strcat attstr (cdr (assoc 2 attdata)) "=" (cdr (assoc 1 attdata)) ";"))
                  )
                  (setq attent (entnext attent))
                )
              )
            )
            
            (write-line (strcat (vl-prin1-to-string effname) "\t"
                                (vl-prin1-to-string bname) "\t"
                                lay "\t"
                                (rtos (car pt) 2 4) "\t"
                                (rtos (cadr pt) 2 4) "\t"
                                (rtos (caddr pt) 2 4) "\t"
                                (rtos rot 2 6) "\t"
                                (rtos scx 2 4) "\t"
                                (rtos scy 2 4) "\t"
                                (rtos scz 2 4) "\t"
                                attstr) f)
          )
        )
        (setq i (1+ i))
      )
    )
  )
  
  (write-line "[POLYLINES]" f)
  (write-line "Handle\tLayer\tClosed\tVertices" f)
  (setq ss (ssget "X" '((0 . "*POLYLINE"))))
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (if ent
          (progn
            (setq elist (entget ent))
            (setq lay (cdr (assoc 8 elist)))
            (setq handle (cdr (assoc 5 elist)))
            (setq closed (if (= 1 (logand 1 (cdr (assoc 70 elist)))) "1" "0"))
            
            (setq vstr "")
            (foreach item elist
              (if (= (car item) 10)
                (setq vstr (strcat vstr (rtos (cadr item) 2 4) "," (rtos (caddr item) 2 4) ";"))
              )
            )
            
            (write-line (strcat handle "\t" lay "\t" closed "\t" vstr) f)
          )
        )
        (setq i (1+ i))
      )
    )
  )
  
  (close f)
  (princ "\nExtraction Done Successfully!\n")
  (command "_.QUIT" "_Y")
)
(c:ExportCadData)
