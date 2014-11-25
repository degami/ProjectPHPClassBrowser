<?php

array_shift($argv);
foreach($argv as $filepath){
  if(file_exists($filepath)){
    $filecontent = implode("\n",file($filepath));
    $classes = get_php_classes_with_methods($filecontent);
    foreach ($classes as $key => $classdef) {
      if(empty($classdef['classname'])) continue;
      foreach ($classdef['classmethods'] as $classmethod) {
        $line_method = ceil( $classmethod['line'] / 2 );
        $line_class = ceil( $classdef['line'] / 2 );
        $spanfromclass = ( $line_method - $line_class);
        print $filepath.';['.$line_class.'-'.$spanfromclass.'];'.$classdef['classname'].';'.$classmethod['name'].';'.trim(rtrim($classmethod['args'],';')).';'.((isset($classmethod['visibility'])) ? $classmethod['visibility']:'private').';'.(($classmethod['context'] == NULL) ? '':$classmethod['context'])."\n";
      }
    }
  }
}

function get_php_classes_with_methods($php_code) {
  $classes = array();
  $tokens = token_get_all($php_code);
  $class_methods = array();
  $current_class_name = '';
  $current_function_definition = NULL;
  $function_args = NULL;
  $wait_for_function_name = FALSE;
  $wait_for_open_braket = FALSE;
  $open_brakets_counter = 0;
  $start_count_brakets = FALSE;
  $in_class_definition = FALSE;
  $current_class_line = $currline = 0;
  for ($i = 0; $i < count($tokens); $i++) {
    // if( ($tokens[$i][0] == T_WHITESPACE || $tokens[$i][0] == T_COMMENT) && preg_match("/\n/msi", $tokens[$i][1]) ) {
    if( is_array($tokens[$i]) && preg_match("/\n/msi", $tokens[$i][1]) ) {
      // var_dump($tokens[$i]);var_dump(token_name($tokens[$i][0]));
      $countnewlines = substr_count( $tokens[$i][1], "\n" );
      if($countnewlines < 0) $countnewlines = 0;
      $currline += $countnewlines;
      // print "found {$countnewlines} newlines - currline : {$currline}\n";
    }

    if ( $i >= 2 && $tokens[$i - 2][0] == T_CLASS
        && $tokens[$i - 1][0] == T_WHITESPACE
        && $tokens[$i][0] == T_STRING) {

        if(!empty($class_methods)){
          $classes[] = array('classname'=>$current_class_name, 'classmethods' => $class_methods , 'line' => $current_class_line + 1);
        }

        $current_class_name = $tokens[$i][1]; $current_class_line = $currline;
        // print "found class: {$current_class_name}\n";
        $class_methods = array();
        $start_count_brakets = TRUE;
        $open_brakets_counter = 0;
    }

    // print "\$open_brakets_counter: {$open_brakets_counter}\n";

    if( $start_count_brakets == TRUE && ($tokens[$i][0] == '{' || $tokens[$i][0] == T_CURLY_OPEN)) {
      $open_brakets_counter++;
    }
    if( $start_count_brakets == TRUE && $tokens[$i][0] == '}' ) {
      $open_brakets_counter--;
    }

    if( $in_class_definition == TRUE && $open_brakets_counter == 0){
      $start_count_brakets = FALSE;
    }

    if( $start_count_brakets == TRUE && $open_brakets_counter > 0 ){
      $in_class_definition = TRUE;
    }else{
      $open_brakets_counter = 0;
      $in_class_definition = FALSE;
    }

    if($in_class_definition == TRUE){
      if( $tokens[$i][0] == T_PRIVATE || $tokens[$i][0] == T_PUBLIC || $tokens[$i][0] == T_PROTECTED ){
        if(!is_array($current_function_definition)) $current_function_definition = array();
        $current_function_definition += array( 'visibility' => ($tokens[$i][0] == T_PRIVATE) ? 'private' : (($tokens[$i][0] == T_PROTECTED) ? 'protected' : 'public') );
      }
      if( $tokens[$i][0] == T_STATIC || $tokens[$i][0] == T_ABSTRACT ){
        if(!is_array($current_function_definition)) $current_function_definition = array();
        $current_function_definition += array( 'context' => ($tokens[$i][0] == T_STATIC) ? 'static' : 'abstract' );
      }

      if($tokens[$i][0] == T_FUNCTION){
        $wait_for_function_name = TRUE;
      }

      if($wait_for_function_name == TRUE && $tokens[$i][0] == T_STRING){
        if(!is_array($current_function_definition)) $current_function_definition = array();
        $current_function_definition += array( 'name' => $tokens[$i][1] , 'line' => $currline + 1 );
        $wait_for_function_name = FALSE;
        $wait_for_open_braket = TRUE;
      }else if($tokens[$i][0] != '{' && $wait_for_open_braket == TRUE){
        if( $tokens[$i][0] == T_WHITESPACE && $tokens[$i][1] == "\n" ) continue;
        if( $tokens[$i][0] == T_COMMENT ) continue;
        $function_args .= (is_array($tokens[$i])) ? $tokens[$i][1] : $tokens[$i];
      }


      if( $wait_for_function_name == FALSE && $wait_for_open_braket == FALSE && ($tokens[$i][0] == '{' || $tokens[$i][0] == ';') ){
        // T_FUNCTION not found, maybe it is not a function?
        $wait_for_open_braket = FALSE;
        $wait_for_function_name = FALSE;
        $current_function_definition = NULL;
        $function_args = NULL;
      }

      if(($tokens[$i][0] == '{' || $tokens[$i][0] == ';') && $wait_for_open_braket == TRUE){
        if(isset($current_function_definition['name']) && !empty($current_function_definition['name'])){
          $current_function_definition += array( 'args' => trim($function_args) );
          $current_function_definition += array( 'context' => NULL );
          $class_methods[] = $current_function_definition;
        }
        $wait_for_open_braket = FALSE;
        $current_function_definition = NULL;
        $function_args = NULL;
      }
    }

  }
  //add last class
  if( count($classes) == 0 || (count($classes) > 0 && $classes[count($classes)-1]['classname'] != $current_class_name)){
      if(!empty($class_methods)){
        $classes[] = array('classname'=>$current_class_name, 'classmethods' => $class_methods , 'line' => $current_class_line + 1);
      }
  }
  return $classes;
}
