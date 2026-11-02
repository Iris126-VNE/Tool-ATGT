(vl-load-com)
(setq ss (ssget "X"))
(if ss
  (progn
    (setq ent (ssname ss 0))
    (vla-getboundingbox (vlax-ename->vla-object ent) 'minpt 'maxpt)
    (setq f (open "H:/My Drive/1.Work/ATGT/Tool ATGT/dpc_bbox.txt" "w"))
    (write-line (strcat "MIN=" (vl-prin1-to-string (vlax-safearray->list minpt))) f)
    (write-line (strcat "MAX=" (vl-prin1-to-string (vlax-safearray->list maxpt))) f)
    (close f)
  )
)
(command "_.QUIT" "_Y")